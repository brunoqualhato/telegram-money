"""Serviço de gerenciamento de fila de processamento e limites de concorrência."""

from datetime import timedelta
from sqlalchemy import and_, delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from ..config import settings
from ..db import utcnow
from ..models import Document, ProcessingJob, ResourceLease
from .settings import get_app_setting
from .resources import resource_slot


def _active_job(db, job_type, target_id):
    return db.scalar(select(ProcessingJob).where(
        ProcessingJob.job_type == job_type, ProcessingJob.target_id == target_id,
        ProcessingJob.status.in_(["pending", "running"]),
    ))


def enqueue_job(
    db,
    category: str = "ai",
    job_type: str = "ai_document_summary",
    title: str = "",
    target_id: str | None = None,
    priority: int = 0,
    payload: dict | None = None,
) -> ProcessingJob:
    """Enfileira uma tarefa garantindo unicidade para tarefas ativas do mesmo alvo."""
    if target_id:
        existing = _active_job(db, job_type, target_id)
        if existing:
            return existing

    job = ProcessingJob(
        category=category,
        job_type=job_type,
        title=title or f"Processamento · {job_type}",
        target_id=target_id,
        status="pending",
        priority=priority,
        payload=payload,
        created_at=utcnow(),
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _active_job(db, job_type, target_id)
        if not existing:
            raise
        return existing
    return job


def get_queue_stats(db) -> dict:
    """Retorna estatísticas consolidadas e métricas da fila."""
    counts = dict(
        db.execute(
            select(ProcessingJob.status, func.count(ProcessingJob.id)).group_by(ProcessingJob.status)
        ).all()
    )
    is_paused = get_app_setting("ai_queue_paused", "false", db=db).lower() == "true"
    max_ai = int(get_app_setting("max_ai_concurrency", "1", db=db) or "1")
    max_api = int(get_app_setting("max_api_concurrency", "2", db=db) or "2")
    ai_timeout = int(get_app_setting("ai_job_timeout_seconds", "120", db=db) or "120")
    api_poll = int(get_app_setting("poll_seconds", str(settings().poll_seconds), db=db))

    return {
        "pending": counts.get("pending", 0),
        "running": counts.get("running", 0),
        "completed": counts.get("completed", 0),
        "failed": counts.get("failed", 0),
        "cancelled": counts.get("cancelled", 0),
        "total": sum(counts.values()),
        "ai_queue_paused": is_paused,
        "max_ai_concurrency": max_ai,
        "max_api_concurrency": max_api,
        "ai_job_timeout_seconds": ai_timeout,
        "api_poll_interval_seconds": api_poll,
    }


def list_jobs(db, status: str | None = None, category: str | None = None, limit: int = 100, offset: int = 0):
    """Lista tarefas da fila com suporte a filtros e ordenação por prioridade e data."""
    query = select(ProcessingJob)
    if status and status != "all":
        query = query.where(ProcessingJob.status == status)
    if category and category != "all":
        query = query.where(ProcessingJob.category == category)

    # Ordena tarefas pendentes/em execução primeiro, respeitando prioridade e data
    query = query.order_by(
        ProcessingJob.status.in_(["running", "pending"]).desc(),
        ProcessingJob.priority.desc(),
        ProcessingJob.created_at.desc(),
    ).offset(offset).limit(limit)

    return db.scalars(query).all()


def _locked_job(db, job_id):
    db.execute(update(ProcessingJob).where(ProcessingJob.id == job_id).values(status=ProcessingJob.status))
    db.expire_all()
    return db.get(ProcessingJob, job_id)


def cancel_job(db, job_id: int) -> ProcessingJob | None:
    """Cancela uma tarefa pendente ou em execução."""
    job = _locked_job(db, job_id)
    if not job:
        return None
    if job.status in ("pending", "running"):
        job.status = "cancelled"
        job.completed_at = utcnow()
        job.error = "Cancelado pelo usuário"
        if job.job_type == "ai_document_summary" and job.target_id:
            doc = db.get(Document, int(job.target_id))
            if doc and not doc.summary:
                doc.status, doc.error = "cancelled", "Resumo cancelado pelo usuário"
        db.commit()
    return job


def retry_job(db, job_id: int) -> ProcessingJob | None:
    """Reenfileira uma tarefa com falha ou cancelada."""
    job = _locked_job(db, job_id)
    if not job:
        return None
    if job.status not in ("failed", "cancelled"):
        return job
    active = _active_job(db, job.job_type, job.target_id) if job.target_id else None
    if active:
        return active
    job.status = "pending"
    job.error = None
    job.started_at = None
    job.completed_at = None
    job.execution_token = None
    if job.category == "ai" and job.target_id:
        doc = db.get(Document, int(job.target_id))
        if doc:
            doc.status = "pending"
            doc.error = None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        active = _active_job(db, job.job_type, job.target_id)
        if not active:
            raise
        return active
    return job


def prioritize_job(db, job_id: int) -> ProcessingJob | None:
    """Aumenta a prioridade da tarefa na fila."""
    job = db.get(ProcessingJob, job_id)
    if not job:
        return None
    job.priority += 10
    db.commit()
    return job


def clear_completed_jobs(db) -> int:
    """Remove tarefas concluídas e canceladas do histórico."""
    res = db.execute(delete(ProcessingJob).where(ProcessingJob.status.in_(["completed", "cancelled"])))
    db.commit()
    return res.rowcount or 0


def sync_pending_documents(db):
    """Garante que documentos com status pending tenham entrada na fila de processamento de IA."""
    pending_docs = db.scalars(
        select(Document).where(Document.status == "pending").order_by(Document.id)
    ).all()
    for doc in pending_docs:
        enqueue_job(
            db,
            category="ai",
            job_type="ai_document_summary",
            title=f"Resumo IA · {doc.ticker} - {doc.title[:45]}",
            target_id=str(doc.id),
            payload={"ticker": doc.ticker, "title": doc.title},
        )


def _cleanup_stale_jobs(db, timeout_seconds: int):
    stale_limit = utcnow() - timedelta(seconds=max(60, timeout_seconds + 30))
    live_lease = exists().where(ResourceLease.token == ProcessingJob.execution_token, ResourceLease.expires_at > utcnow())
    stale_jobs = db.scalars(
        select(ProcessingJob).where(
            ProcessingJob.status == "running",
            or_(
                and_(ProcessingJob.execution_token.is_(None), ProcessingJob.started_at < stale_limit),
                and_(ProcessingJob.execution_token.is_not(None), ~live_lease),
            ),
        )
    ).all()
    for job in stale_jobs:
        claimed = db.execute(update(ProcessingJob).where(
            ProcessingJob.id == job.id, ProcessingJob.status == "running",
            ProcessingJob.execution_token == job.execution_token,
        ).values(status="failed")).rowcount
        if not claimed:
            continue
        job.status = "failed"
        job.error = "Tempo limite de execução excedido"
        job.completed_at = utcnow()
        if job.job_type == "ai_document_summary" and job.target_id:
            doc = db.get(Document, int(job.target_id))
            if doc and not doc.summary:
                doc.status, doc.error = "failed", job.error
    if stale_jobs:
        db.commit()


def _execute_ai_job(db, job: ProcessingJob, client=None, timeout=None) -> bool:
    job_id = job.id
    token = job.execution_token
    try:
        if job.job_type == "ai_document_summary" and job.target_id:
            from .documents import summarize_document

            doc_id = int(job.target_id)
            summarize_document(db, doc_id, client=client, timeout=timeout, job_id=job_id, execution_token=token)
            db.expire_all()
            current = db.get(ProcessingJob, job_id)
            if current and current.status == "completed" and current.execution_token == token:
                return True
            if not current or current.status != "running" or current.execution_token != token:
                return False
            doc = db.get(Document, doc_id)
            if doc and doc.status == "ready":
                job.status = "completed"
                job.completed_at = utcnow()
                job.error = None
                db.commit()
                return True
            job.status = "failed"
            job.completed_at = utcnow()
            job.error = (doc.error if doc else None) or "Falha ao gerar resumo verificável com IA"
            db.commit()
            return False

        job.status = "completed"
        job.completed_at = utcnow()
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        db.expire_all()
        current = db.get(ProcessingJob, job_id)
        if not current or current.status != "running" or current.execution_token != token:
            return False
        job.status = "failed"
        job.completed_at = utcnow()
        job.error = f"Falha no processamento ({type(exc).__name__})."
        db.commit()
        return False


def dispatch_queue(db, client=None) -> list[dict]:
    """Processa tarefas respeitando pausa, slots de concorrência e timeouts."""
    if settings().demo_mode:
        return []
    timeout = int(get_app_setting("ai_job_timeout_seconds", "120", db=db) or "120")
    _cleanup_stale_jobs(db, timeout)
    sync_pending_documents(db)

    is_paused = get_app_setting("ai_queue_paused", "false", db=db).lower() == "true"
    if is_paused:
        return []

    max_ai = int(get_app_setting("max_ai_concurrency", "1", db=db) or "1")
    running_ai = (
        db.scalar(
            select(func.count(ProcessingJob.id)).where(
                ProcessingJob.category == "ai",
                ProcessingJob.status == "running",
            )
        )
        or 0
    )

    available_slots = max(0, max_ai - running_ai)
    if available_slots <= 0:
        return []

    pending_jobs = db.scalars(
        select(ProcessingJob)
        .where(ProcessingJob.category == "ai", ProcessingJob.status == "pending")
        .order_by(ProcessingJob.priority.desc(), ProcessingJob.created_at.asc())
        .limit(available_slots)
    ).all()

    dispatched = []
    for job in pending_jobs:
        with resource_slot(db, "ai", timeout + 30) as token:
            if not token:
                break
            claimed = db.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job.id, ProcessingJob.status == "pending")
                .values(status="running", started_at=utcnow(), attempts=ProcessingJob.attempts + 1, execution_token=token)
            ).rowcount
            db.commit()
            if not claimed:
                continue
            db.refresh(job)
            job_id, title = job.id, job.title
            success = _execute_ai_job(db, job, client=client, timeout=timeout)
            dispatched.append({"id": job_id, "title": title, "success": success})
            # Cada despacho executa uma tarefa; paralelismo vem de executores distintos.
            break

    return dispatched
