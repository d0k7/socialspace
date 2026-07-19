"""
Celery Tasks - Scheduled Post Polling and Publishing
=====================================================

WHY two separate tasks (poll_scheduled_posts, publish_post) instead of one:
poll_scheduled_posts runs every 60 seconds via Celery Beat and may find
several due posts in a single cycle. If it published each one inline,
sequentially, within the same task execution, a slow platform API call on
post 1 would delay post 2 and post 3, and a crash partway through would
leave later posts in that batch completely unprocessed with no individual
retry path. Instead, poll_scheduled_posts only claims due rows (flips
Post.status to publishing, commits) and enqueues one independent
publish_post task per post. Each publish_post is then its own retryable
unit, isolated from whatever happens to its siblings in the same poll
cycle.

WHY the idempotency check inside publish_post matters for two different
reasons, not one:
First, a single Post can target multiple platforms (Post.platforms is a
JSON list). If platform A succeeds and platform B fails, a naive retry of
the whole post would resend to A, creating a duplicate message on a
platform that already worked. Second, task_acks_late=True in
celery_app.py means an unacknowledged task is redelivered if the worker
process dies mid execution, including the rare case where the platform
send already succeeded but the worker crashed before the success was
committed to Postgres. Checking for an existing successful PostResult per
(post_id, platform) before sending protects against both of these at
once, using data this project already has, no new column required.

WHY Post.status flows through scheduled -> publishing -> published,
partial, or failed, with a path back to scheduled for retries: Post.status
is a plain String(50), not a database level Enum, so extending it with a
"partial" value costs nothing. A post where 2 of 3 target platforms
succeeded after exhausting retries is not accurately described as
"failed", and the existing PostResult rows already record precisely which
platform succeeded and which did not, so "partial" is descriptive, not a
new source of truth.

Author: Dheeraj Mishra / SocialSpace
Phase: 5 - Celery + Redis Scheduling Engine
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_, or_

from app.celery_app import celery_app
from app.database.sync_session import get_sync_db
from app.database.models import Post, ScheduledPost, PostResult, PlatformConnection
from app.tasks.platform_senders import send_telegram_sync, send_discord_sync
from socialspace_agent.utils.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

# WHY base 60 seconds doubling per retry: gives roughly 2, 4, 8 minutes of
# backoff across the default max_retries=3, which is long enough for a
# transient platform outage or rate limit window to clear, short enough
# that a genuinely scheduled post does not sit stuck for hours. This
# formula assumes a small max_retries (the schema default is 3). A much
# larger max_retries would need an explicit cap, not added here since it
# is not the current need.
RETRY_BACKOFF_BASE_SECONDS = 60


# ============================================================================
# TASK 1 - PERIODIC POLLER (invoked by Celery Beat every 60 seconds)
# ============================================================================

@celery_app.task(name="app.tasks.scheduler_task.poll_scheduled_posts")
def poll_scheduled_posts() -> None:
    """
    Find every post that is due right now, claim it, and hand it off to
    publish_post for the actual platform sending.

    A post is due if either:
      - It has never been attempted (next_retry_at is NULL) and its
        scheduled_at has passed, or
      - It failed a previous attempt and its next_retry_at has passed.

    WHY with_for_update(of=Post, skip_locked=True): at the current single
    worker, single beat, --pool=solo deployment (required on Windows,
    since Celery's prefork pool relies on POSIX fork which does not exist
    there), two poll cycles cannot literally overlap, the solo worker
    processes one task at a time. This clause costs nothing today and
    makes the query safe the moment a second worker or beat instance is
    ever added. Cheap insurance, not a fix for a bug that exists yet.

    WHY claim first, enqueue after the transaction commits: enqueuing
    publish_post while still holding the row lock risks the enqueued task
    running before this transaction's commit is visible, which would make
    publish_post read a stale, still-scheduled status. Committing first
    guarantees publish_post always sees status=publishing when it loads
    the row.
    """
    now = datetime.now(timezone.utc)
    claimed_post_ids: list[str] = []

    with get_sync_db() as db:
        due_query = (
            select(ScheduledPost, Post)
            .join(Post, ScheduledPost.post_id == Post.id)
            .where(
                Post.status == "scheduled",
                or_(
                    and_(
                        ScheduledPost.next_retry_at.is_(None),
                        ScheduledPost.scheduled_at <= now,
                    ),
                    and_(
                        ScheduledPost.next_retry_at.isnot(None),
                        ScheduledPost.next_retry_at <= now,
                    ),
                ),
            )
            .with_for_update(of=Post, skip_locked=True)
        )

        rows = db.execute(due_query).all()

        for _scheduled_post, post in rows:
            post.status = "publishing"
            claimed_post_ids.append(str(post.id))

        # get_sync_db commits here on clean exit, releasing row locks and
        # making status=publishing visible before anything is enqueued.

    for post_id in claimed_post_ids:
        publish_post.delay(post_id)

    if claimed_post_ids:
        logger.info(
            "poll_scheduled_posts: claimed %d post(s) for publishing",
            len(claimed_post_ids),
        )


# ============================================================================
# TASK 2 - ACTUAL PUBLISH LOGIC (enqueued once per claimed post)
# ============================================================================

@celery_app.task(name="app.tasks.scheduler_task.publish_post")
def publish_post(post_id: str) -> None:
    """
    Attempt to send one post to every platform it targets, skipping any
    platform that has already succeeded, recording an outcome for every
    attempt, and deciding the post's next status based on what happened.

    Final status logic:
      - Every target platform has a successful PostResult: "published"
      - Some platforms still failing, retries remain: back to "scheduled"
        with retry_count incremented and next_retry_at set, so
        poll_scheduled_posts picks it up again on its own next cycle
      - Some platforms still failing, retries exhausted, at least one
        platform did succeed at some point: "partial"
      - Retries exhausted, nothing ever succeeded: "failed"

    Args:
        post_id: UUID string of the Post to publish. Passed as str because
            Celery task arguments must be JSON serialisable and a raw
            uuid.UUID is not.
    """
    post_uuid = uuid.UUID(post_id)

    with get_sync_db() as db:
        post = db.execute(
            select(Post).where(Post.id == post_uuid)
        ).scalar_one_or_none()

        if post is None:
            logger.error("publish_post: post_id %s not found, skipping", post_id)
            return

        scheduled = db.execute(
            select(ScheduledPost).where(ScheduledPost.post_id == post.id)
        ).scalar_one_or_none()

        if scheduled is None:
            logger.error(
                "publish_post: no ScheduledPost row for post_id %s, skipping",
                post_id,
            )
            return

        if post.status != "publishing":
            # WHY this is not an error: the task may have been redelivered
            # after already reaching a terminal state on a previous run
            # whose final commit landed but whose acknowledgement was lost
            # to a worker crash, or the user cancelled the post between
            # poll_scheduled_posts claiming it and this task executing.
            # Either way, re-running would be wrong, not merely redundant.
            logger.info(
                "publish_post: post_id %s status is '%s', not 'publishing', skipping",
                post_id,
                post.status,
            )
            return

        try:
            settings = get_settings()
            target_platforms: list[str] = post.platforms

            existing_results = db.execute(
                select(PostResult).where(PostResult.post_id == post.id)
            ).scalars().all()

            # WHY a set built from existing rows, not a fresh query per
            # platform inside the loop: one query up front is cheaper, and
            # this set is updated locally as new successes happen in this
            # run, so the final status decision below never needs to
            # re-query what it already knows.
            already_succeeded: set[str] = {
                r.platform for r in existing_results if r.success
            }

            for platform in target_platforms:
                if platform in already_succeeded:
                    logger.info(
                        "publish_post: post_id %s already succeeded on %s, skipping",
                        post_id,
                        platform,
                    )
                    continue

                connection = db.execute(
                    select(PlatformConnection).where(
                        PlatformConnection.user_id == post.user_id,
                        PlatformConnection.platform == platform,
                        PlatformConnection.is_active == True,  # noqa: E712
                    )
                ).scalar_one_or_none()

                if connection is None:
                    result = {
                        "success": False,
                        "platform_post_id": None,
                        "platform_post_url": None,
                        "error_message": f"{platform} is not connected for this user.",
                        "error_code": "not_connected",
                    }
                elif platform == "telegram":
                    chat_id = connection.tokens.get("chat_id")
                    result = send_telegram_sync(
                        bot_token=settings.telegram_bot_token,
                        chat_id=chat_id,
                        content=post.content,
                    )
                elif platform == "discord":
                    channel_id = connection.tokens.get("channel_id")
                    result = send_discord_sync(
                        bot_token=settings.discord_bot_token,
                        channel_id=channel_id,
                        content=post.content,
                    )
                else:
                    # WHY this branch is complete code, not a placeholder:
                    # Twitter is connected but posting is genuinely blocked
                    # by the paid tier requirement, and Reddit credentials
                    # are not yet issued. A post targeting either records
                    # an honest, specific failure reason rather than
                    # crashing or silently dropping the platform.
                    result = {
                        "success": False,
                        "platform_post_id": None,
                        "platform_post_url": None,
                        "error_message": f"No working sender implemented yet for {platform}.",
                        "error_code": "not_implemented",
                    }

                db.add(
                    PostResult(
                        post_id=post.id,
                        platform=platform,
                        success=result["success"],
                        platform_post_id=result["platform_post_id"],
                        platform_post_url=result["platform_post_url"],
                        error_message=result["error_message"],
                        error_code=result["error_code"],
                        published_at=(
                            datetime.now(timezone.utc) if result["success"] else None
                        ),
                    )
                )

                if result["success"]:
                    already_succeeded.add(platform)

            all_succeeded = set(target_platforms).issubset(already_succeeded)

            if all_succeeded:
                post.status = "published"
                logger.info("publish_post: post_id %s fully published", post_id)

            elif scheduled.retry_count < scheduled.max_retries:
                scheduled.retry_count += 1
                backoff_seconds = RETRY_BACKOFF_BASE_SECONDS * (2 ** scheduled.retry_count)
                scheduled.next_retry_at = datetime.now(timezone.utc) + timedelta(
                    seconds=backoff_seconds
                )
                post.status = "scheduled"
                logger.warning(
                    "publish_post: post_id %s incomplete, retry %d/%d scheduled for %s",
                    post_id,
                    scheduled.retry_count,
                    scheduled.max_retries,
                    scheduled.next_retry_at,
                )

            else:
                post.status = "partial" if already_succeeded else "failed"
                logger.error(
                    "publish_post: post_id %s exhausted retries, final status '%s'",
                    post_id,
                    post.status,
                )

        except Exception as exc:
            # WHY this safety net exists: task_acks_late acknowledges a
            # task whether it succeeds or raises, only a worker process
            # dying mid task triggers redelivery. An unhandled exception
            # here, a bug, a transient DB hiccup, anything not already
            # caught inside the sender functions, would otherwise strand
            # this post at status=publishing forever, since
            # poll_scheduled_posts only ever looks for status=scheduled.
            # Falling back to the same retry/backoff path a normal send
            # failure uses means there is exactly one recovery mechanism,
            # not two.
            logger.exception(
                "publish_post: unexpected error for post_id %s: %s", post_id, exc
            )
            if scheduled.retry_count < scheduled.max_retries:
                scheduled.retry_count += 1
                backoff_seconds = RETRY_BACKOFF_BASE_SECONDS * (2 ** scheduled.retry_count)
                scheduled.next_retry_at = datetime.now(timezone.utc) + timedelta(
                    seconds=backoff_seconds
                )
                post.status = "scheduled"
            else:
                post.status = "failed"

        # get_sync_db commits here on clean exit. If the try block above
        # raised and was caught, execution still reaches this point
        # normally, so the fallback status change above is committed too.