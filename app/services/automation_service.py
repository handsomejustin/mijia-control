from datetime import datetime, timezone

from app.extensions import db
from app.models.automation_rule import AutomationRule
from app.services.device_service import DeviceService
from app.services.scene_service import SceneService


class AutomationService:
    @staticmethod
    def list_rules(user_id: int) -> list[dict]:
        rules = AutomationRule.query.filter_by(user_id=user_id).order_by(AutomationRule.id.desc()).all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "is_enabled": r.is_enabled,
                "trigger_type": r.trigger_type,
                "trigger_config": r.trigger_config,
                "action_type": r.action_type,
                "action_config": r.action_config,
                "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rules
        ]

    @staticmethod
    def create_rule(user_id: int, data: dict) -> dict:
        required = ["name", "trigger_type", "trigger_config", "action_type", "action_config"]
        for field in required:
            if field not in data:
                raise ValueError(f"缺少字段: {field}")

        rule = AutomationRule(
            user_id=user_id,
            name=data["name"],
            trigger_type=data["trigger_type"],
            trigger_config=data["trigger_config"],
            action_type=data["action_type"],
            action_config=data["action_config"],
        )
        db.session.add(rule)
        db.session.commit()
        return {"id": rule.id, "name": rule.name}

    @staticmethod
    def update_rule(user_id: int, rule_id: int, data: dict) -> dict:
        rule = AutomationRule.query.filter_by(user_id=user_id, id=rule_id).first()
        if not rule:
            raise ValueError("规则不存在")
        for field in ("name", "trigger_type", "trigger_config", "action_type", "action_config", "is_enabled"):
            if field in data:
                setattr(rule, field, data[field])
        db.session.commit()
        return {"id": rule.id, "name": rule.name}

    @staticmethod
    def delete_rule(user_id: int, rule_id: int) -> None:
        rule = AutomationRule.query.filter_by(user_id=user_id, id=rule_id).first()
        if not rule:
            raise ValueError("规则不存在")
        db.session.delete(rule)
        db.session.commit()

    @staticmethod
    def toggle_rule(user_id: int, rule_id: int) -> dict:
        rule = AutomationRule.query.filter_by(user_id=user_id, id=rule_id).first()
        if not rule:
            raise ValueError("规则不存在")
        rule.is_enabled = not rule.is_enabled
        db.session.commit()
        return {"id": rule.id, "is_enabled": rule.is_enabled}

    @staticmethod
    def execute_rule(rule: AutomationRule) -> bool:
        if not rule.is_enabled:
            return False
        try:
            if rule.action_type == "set_property":
                cfg = rule.action_config
                DeviceService.set_property(
                    rule.user_id, cfg["did"], cfg["prop_name"], cfg["value"]
                )
            elif rule.action_type == "run_scene":
                cfg = rule.action_config
                SceneService.run_scene(rule.user_id, cfg["scene_id"])
            else:
                return False
            rule.last_triggered_at = datetime.now(timezone.utc)
            db.session.commit()
            return True
        except Exception:
            return False

    @staticmethod
    def get_cron_rules() -> list[AutomationRule]:
        return AutomationRule.query.filter_by(trigger_type="cron", is_enabled=True).all()

    @staticmethod
    def get_interval_rules() -> list[AutomationRule]:
        return AutomationRule.query.filter_by(trigger_type="interval", is_enabled=True).all()
