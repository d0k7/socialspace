"""
One-off password reset script.
Run once from backend/ with venv active, then delete.

WHY this script exists: no forgot-password endpoint exists in auth.py
(only register, login, refresh, me, logout). This is a local dev database
under full control, so a direct reset via the app's own hash_password
function is correct, not a workaround, it produces a hash verify_password
will accept exactly like a normal registration would have.

WHY get_sync_db() and not a raw psycopg2 connection: reuses the exact
sync engine already proven correct by the Celery worker, rather than a
second, separately written DB connection that could drift out of sync
with the real DATABASE_URL handling in sync_session.py.

WHY no explicit db.commit(): get_sync_db() auto-commits on clean exit,
same rule as every Celery task body, an explicit commit here would be
redundant, not wrong, but inconsistent with the established pattern.
"""

from app.auth.security import hash_password
from app.database.sync_session import get_sync_db
from app.database.models import User

EMAIL = "dheeraj2@test.com"
NEW_PASSWORD = "dheeraj07"

with get_sync_db() as db:
    user = db.query(User).filter(User.email == EMAIL).first()
    if user is None:
        print(f"No user found with email {EMAIL}")
    else:
        user.hashed_password = hash_password(NEW_PASSWORD)
        print(f"Password reset for {EMAIL}")
