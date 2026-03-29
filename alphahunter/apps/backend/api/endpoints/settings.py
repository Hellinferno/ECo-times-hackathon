"""Settings endpoint — read and update runtime system settings.

Routes:
  GET    ""  Merge DB SystemSetting rows with DEFAULT_SYSTEM_SETTINGS and return all keys
  PATCH  ""  Bulk-update known setting keys (unknown keys are silently ignored)
"""
from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.db import SystemSetting
from utils.runtime_settings import DEFAULT_SYSTEM_SETTINGS

router = APIRouter()


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    """Retrieve all system settings, merging DB rows with compiled defaults."""
    db_settings = db.query(SystemSetting).all()
    settings_map = {s.key: s.value for s in db_settings}

    # Fill in any keys missing from the DB with their defaults
    result = {key: settings_map.get(key, default) for key, default in DEFAULT_SYSTEM_SETTINGS.items()}

    return {"success": True, "data": result}


@router.patch("")
def update_settings(updates: dict, db: Session = Depends(get_db)):
    """Update system settings. Only accepts known setting keys."""
    updated_keys = []

    for key, value in updates.items():
        if key not in DEFAULT_SYSTEM_SETTINGS:
            continue

        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if existing:
            existing.value = str(value)
            existing.updated_at = datetime.datetime.utcnow()
        else:
            db.add(SystemSetting(
                key=key,
                value=str(value),
                description=f"Auto-created setting for {key}",
            ))
        updated_keys.append(key)

    db.commit()

    return {"success": True, "data": {"updated": updated_keys}}
