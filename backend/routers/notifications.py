"""
Notification Scheduler & Endpoints
------------------------------------
Manages dose reminders and in-app notifications.

Endpoints:
    GET  /notifications                → list unread + recent
    POST /notifications/schedule       → schedule a dose reminder
    POST /notifications/mark-read      → mark notifications as read
    DELETE /notifications/{id}         → delete a notification
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from routers.users import get_current_user

router = APIRouter()

# In-memory store (production: replace with DB table)
_notifications: dict[str, list] = {}  # user_id → list of notification dicts


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ScheduleReminderRequest(BaseModel):
    compound_id: str
    display_name: str
    time_of_day: str          # "08:00", "13:00", "21:00"
    days: List[str]           # ["Mon", "Tue", ...] or ["daily"]
    dose_label: Optional[str] = None   # "1 capsule", "500mg"


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


class NotificationOut(BaseModel):
    id: str
    type: str          # "dose_reminder" | "system" | "insight"
    title: str
    body: str
    compound_id: Optional[str] = None
    is_read: bool
    created_at: str
    scheduled_for: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_user_notifs(user_id: str) -> list:
    return _notifications.setdefault(user_id, [])


def _make_notif(ntype: str, title: str, body: str, **extra) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": ntype,
        "title": title,
        "body": body,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=List[NotificationOut])
async def list_notifications(current_user: dict = Depends(get_current_user)):
    """Return all notifications for this user, unread first."""
    notifs = _get_user_notifs(current_user["user_id"])
    sorted_notifs = sorted(notifs, key=lambda n: (n["is_read"], n["created_at"]), reverse=False)
    return [NotificationOut(**n) for n in sorted_notifs[:50]]


@router.post("/schedule", response_model=NotificationOut, status_code=201)
async def schedule_reminder(
    body: ScheduleReminderRequest,
    current_user: dict = Depends(get_current_user),
):
    """Schedule a recurring dose reminder for a supplement/drug."""
    days_label = ", ".join(body.days) if body.days != ["daily"] else "every day"
    dose = body.dose_label or "your dose"
    notif = _make_notif(
        ntype="dose_reminder",
        title=f"Reminder set: {body.display_name}",
        body=f"You'll be reminded to take {dose} of {body.display_name} at {body.time_of_day} {days_label}.",
        compound_id=body.compound_id,
        scheduled_for=body.time_of_day,
    )
    _get_user_notifs(current_user["user_id"]).append(notif)
    return NotificationOut(**notif)


@router.post("/mark-read")
async def mark_read(
    body: MarkReadRequest,
    current_user: dict = Depends(get_current_user),
):
    """Mark specified notifications as read."""
    notifs = _get_user_notifs(current_user["user_id"])
    for n in notifs:
        if n["id"] in body.notification_ids:
            n["is_read"] = True
    return {"marked": len(body.notification_ids)}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a notification."""
    uid = current_user["user_id"]
    before = len(_notifications.get(uid, []))
    _notifications[uid] = [n for n in _notifications.get(uid, []) if n["id"] != notification_id]
    deleted = before - len(_notifications[uid])
    return {"deleted": deleted}


# ─── Internal: push a system notification ─────────────────────────────────────

def push_insight_notification(user_id: str, title: str, body: str):
    """Called internally by scorer/projector when a critical insight is detected."""
    notif = _make_notif(ntype="insight", title=title, body=body)
    _get_user_notifs(user_id).append(notif)
