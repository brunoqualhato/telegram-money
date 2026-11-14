from sqlalchemy import select
from .models import AuditLog


def rows(db, model, limit=100):
    order = model.created_at if hasattr(model, "created_at") else model.id
    return db.scalars(select(model).order_by(order.desc(), model.id.desc()).limit(limit)).all()


def audit(db, action, detail):
    db.add(AuditLog(action=action, detail=detail))
