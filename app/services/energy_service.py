from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.extensions import db
from app.models.energy_log import EnergyLog


class EnergyService:
    @staticmethod
    def log_energy(user_id: int, did: str, prop_name: str, value: float, unit: str = None) -> dict:
        log = EnergyLog(user_id=user_id, did=did, prop_name=prop_name, value=value, unit=unit)
        db.session.add(log)
        db.session.commit()
        return {"id": log.id, "value": value}

    @staticmethod
    def get_daily_stats(user_id: int, did: str, days: int = 7) -> list[dict]:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        rows = (
            db.session.query(
                func.date(EnergyLog.logged_at).label("date"),
                func.min(EnergyLog.value).label("min_val"),
                func.max(EnergyLog.value).label("max_val"),
                func.avg(EnergyLog.value).label("avg_val"),
                func.count(EnergyLog.id).label("count"),
            )
            .filter(EnergyLog.user_id == user_id, EnergyLog.did == did, EnergyLog.logged_at >= start)
            .group_by(func.date(EnergyLog.logged_at))
            .order_by(func.date(EnergyLog.logged_at))
            .all()
        )
        return [
            {
                "date": str(r.date),
                "min": round(r.min_val, 2),
                "max": round(r.max_val, 2),
                "avg": round(float(r.avg_val), 2),
                "count": r.count,
            }
            for r in rows
        ]

    @staticmethod
    def get_hourly_stats(user_id: int, did: str, hours: int = 24) -> list[dict]:
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=hours)
        rows = (
            db.session.query(
                func.hour(EnergyLog.logged_at).label("hour"),
                func.avg(EnergyLog.value).label("avg_val"),
                func.min(EnergyLog.value).label("min_val"),
                func.max(EnergyLog.value).label("max_val"),
            )
            .filter(EnergyLog.user_id == user_id, EnergyLog.did == did, EnergyLog.logged_at >= start)
            .group_by(func.hour(EnergyLog.logged_at))
            .order_by(func.hour(EnergyLog.logged_at))
            .all()
        )
        return [
            {"hour": r.hour, "avg": round(float(r.avg_val), 2), "min": round(r.min_val, 2), "max": round(r.max_val, 2)}
            for r in rows
        ]

    @staticmethod
    def get_latest(user_id: int, did: str, prop_name: str = None, limit: int = 100) -> list[dict]:
        query = EnergyLog.query.filter_by(user_id=user_id, did=did)
        if prop_name:
            query = query.filter_by(prop_name=prop_name)
        logs = query.order_by(EnergyLog.logged_at.desc()).limit(limit).all()
        return [
            {
                "id": log.id,
                "prop_name": log.prop_name,
                "value": log.value,
                "unit": log.unit,
                "logged_at": log.logged_at.isoformat() if log.logged_at else None,
            }
            for log in logs
        ]

    @staticmethod
    def get_device_energy_props(user_id: int, did: str) -> list[str]:
        results = (
            db.session.query(EnergyLog.prop_name)
            .filter_by(user_id=user_id, did=did)
            .distinct()
            .all()
        )
        return [r[0] for r in results]
