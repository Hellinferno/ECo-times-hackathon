from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.db import SystemSetting
import datetime
from utils.runtime_settings import DEFAULT_SYSTEM_SETTINGS

router = APIRouter()


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    """Retrieve all system settings."""
    settings = db.query(SystemSetting).all()
    settings_map = {s.key: s.value for s in settings}

    # Merge with defaults for any missing keys
    result = {}
    for key, default_val in DEFAULT_SYSTEM_SETTINGS.items():
        result[key] = settings_map.get(key, default_val)

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
            setting = SystemSetting(
                key=key,
                value=str(value),
                description=f"Auto-created setting for {key}",
            )
            db.add(setting)
        updated_keys.append(key)

    db.commit()

    return {"success": True, "data": {"updated": updated_keys}}
