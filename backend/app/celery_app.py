"""
Celery Application Configuration
=================================

WHY this file exists (separate from main.py):
FastAPI (main.py) and Celery are two independent processes with two independent
entry points. main.py boots uvicorn's ASGI server. This file boots the Celery
app that celery worker and celery beat both import. They share the same
Python package (app/) and the same PostgreSQL database, but they are not the
same running process and never share the async event loop.

WHY Redis as broker but NOT as a result backend:
Redis (Memurai locally) is the broker. It holds the queue of "run this task"
messages. It is disposable by design. If Redis restarts, in flight task
messages that have not been picked up yet are lost, but that is acceptable
here because the actual scheduling truth lives in PostgreSQL
(scheduled_posts.scheduled_at, posts.status), not in Redis. Celery Beat's
polling task rediscovers any due row every 60 seconds regardless of what
Redis remembers.

We deliberately do not configure a Celery result backend. A result backend
would store task return values and state in Redis, a second, weaker copy of
information that already lives durably in PostgreSQL (Post.status,
PostResult rows). Two sources of truth for the same fact is exactly the
anti pattern this project has avoided since Phase 4 (one canonical system
per concern). The task functions write their own outcome directly to
Postgres instead of returning it through Celery.

WHY Celery Beat's schedule lives in code (not django-celery-beat):
This is not a Django project. Celery's built in beat_schedule dictionary is
the standard mechanism for periodic tasks outside Django and requires no
additional database table or package.

WHY --pool=solo is required on Windows (documented at worker startup, not
here): Celery's own documentation states plainly that Windows is not a
supported platform, because the default prefork worker pool relies on
POSIX fork(), which does not exist on Windows. --pool=solo runs the worker
single threaded with no forking. At this project's current scale (a
handful of scheduled posts, not high volume concurrent processing) this is
a real, working setup, not a compromise that costs anything today.

Author: Dheeraj Mishra / SocialSpace
Phase: 5 - Celery + Redis Scheduling Engine
"""

import os
import logging
from datetime import timedelta

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# BROKER CONFIGURATION
# ============================================================================

# WHY default db index 0 stated explicitly: Redis and Memurai both support
# 16 logical databases (0 through 15) on one instance. Being explicit here
# avoids ambiguity if another tool on this machine later also uses Redis on
# a different db number.
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ============================================================================
# CELERY APP INSTANCE
# ============================================================================

celery_app = Celery(
    "socialspace",
    broker=REDIS_URL,
    # WHY backend=None: see file docstring section on result backends.
    # Outcomes live in Postgres, not in a second Redis backed store.
    backend=None,
    include=["app.tasks.scheduler_task"],
)

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

celery_app.conf.update(
    # WHY json not pickle: pickle can execute arbitrary code on deserialize,
    # a real security risk if the broker were ever exposed. json is the
    # modern Celery default. Made explicit here to match this codebase's
    # existing rule of explicit typing and configuration everywhere.
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # WHY UTC: every timestamp in this codebase is stored and computed in
    # UTC (see utcnow() in app/database/models.py). Celery's internal clock
    # must match or Beat's timing math would be off by the IST offset.
    timezone="UTC",
    enable_utc=True,

    # WHY acks_late=True: without this, Celery marks a task as safe to
    # forget the moment a worker PICKS UP the task, not when it finishes.
    # If the worker process crashes mid publish (for example the PowerShell
    # window running it is closed), a task without acks_late is silently
    # lost forever even though the post was never actually sent.
    # acks_late=True delays acknowledgement until the task function returns
    # successfully, so a crashed worker's unfinished task is redelivered to
    # the next worker that starts. This is required for the "close the
    # browser, wake up, the post was sent" guarantee to survive a worker
    # crash, not just a clean shutdown.
    task_acks_late=True,

    # WHY reject_on_worker_lost=True: pairs with acks_late above. If the
    # worker process itself is killed while a task is running (not the task
    # raising a normal exception), this tells the broker to put the task
    # back on the queue instead of assuming it succeeded.
    task_reject_on_worker_lost=True,

    # WHY worker_prefetch_multiplier=1: the Celery default prefetches
    # several tasks per worker ahead of time for throughput. At this scale,
    # a single dev worker running --pool=solo on Windows, prefetching gives
    # no benefit and only risks one worker holding tasks that do not need
    # to wait. Explicit 1 means fetch one task at a time.
    worker_prefetch_multiplier=1,
)

# ============================================================================
# BEAT SCHEDULE - PERIODIC TASKS
# ============================================================================

# WHY 60 second interval: matches the polling cadence already agreed for
# this project. Short enough that a post scheduled for 9:00 AM fires within
# a minute of 9:00 AM. Long enough that idle polling, the common case since
# most 60 second windows have zero due posts, costs one cheap indexed
# Postgres query per minute, not meaningful load.
celery_app.conf.beat_schedule = {
    "poll-scheduled-posts-every-60-seconds": {
        "task": "app.tasks.scheduler_task.poll_scheduled_posts",
        "schedule": timedelta(seconds=60),
    },
}

logger.info("Celery app configured. Broker: %s", REDIS_URL)