from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from ..auth import current_owner
from ..crud import audit
from ..db import get_db
from ..schemas import QueueSettingsInput
from ..services.queue import (
    cancel_job,
    clear_completed_jobs,
    dispatch_queue,
    get_queue_stats,
    list_jobs,
    prioritize_job,
    retry_job,
)
from ..services.settings import get_app_setting, save_settings

router = APIRouter(tags=["queue"])


@router.get("/api/queue")
def get_queue(
    status: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    owner=Depends(current_owner),
    db=Depends(get_db),
):
    stats = get_queue_stats(db)
    jobs = list_jobs(db, status=status, category=category, limit=limit, offset=offset)
    return {
        "stats": stats,
        "settings": {
            "max_ai_concurrency": stats["max_ai_concurrency"],
            "max_api_concurrency": stats["max_api_concurrency"],
            "ai_queue_paused": stats["ai_queue_paused"],
            "ai_job_timeout_seconds": stats["ai_job_timeout_seconds"],
            "api_poll_interval_seconds": stats["api_poll_interval_seconds"],
        },
        "jobs": jsonable_encoder(
            [
                {
                    "id": j.id,
                    "category": j.category,
                    "job_type": j.job_type,
                    "title": j.title,
                    "target_id": j.target_id,
                    "status": j.status,
                    "priority": j.priority,
                    "attempts": j.attempts,
                    "max_attempts": j.max_attempts,
                    "error": j.error,
                    "created_at": j.created_at,
                    "started_at": j.started_at,
                    "completed_at": j.completed_at,
                }
                for j in jobs
            ]
        ),
    }


@router.post("/api/queue/settings")
def update_queue_settings(
    data: QueueSettingsInput,
    owner=Depends(current_owner),
    db=Depends(get_db),
):
    save_settings(
        db,
        {
            "max_ai_concurrency": str(data.max_ai_concurrency),
            "max_api_concurrency": str(data.max_api_concurrency),
            "ai_queue_paused": "true" if data.ai_queue_paused else "false",
            "ai_job_timeout_seconds": str(data.ai_job_timeout_seconds),
            "poll_seconds": str(data.api_poll_interval_seconds),
        },
    )
    audit(
        db,
        "update_queue_settings",
        f"Limites de recursos atualizados: IA={data.max_ai_concurrency}, API={data.max_api_concurrency}, Pausado={data.ai_queue_paused}",
    )
    db.commit()
    return {"ok": True, "settings": data.model_dump()}


@router.post("/api/queue/pause")
def toggle_queue_pause(owner=Depends(current_owner), db=Depends(get_db)):
    current = get_app_setting("ai_queue_paused", "false", db=db).lower() == "true"
    new_state = not current
    save_settings(db, {"ai_queue_paused": "true" if new_state else "false"})
    action = "pausada" if new_state else "retomada"
    audit(db, "toggle_queue_pause", f"Fila de IA {action}")
    db.commit()
    return {"ok": True, "ai_queue_paused": new_state}


@router.post("/api/queue/dispatch")
def trigger_dispatch(owner=Depends(current_owner), db=Depends(get_db)):
    dispatched = dispatch_queue(db)
    return {"ok": True, "dispatched": dispatched, "count": len(dispatched)}


@router.post("/api/queue/{job_id}/cancel")
def cancel_queue_job(job_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    job = cancel_job(db, job_id)
    if not job:
        raise HTTPException(404, "Tarefa não encontrada")
    audit(db, "cancel_job", f"Tarefa #{job_id} cancelada")
    db.commit()
    return {"ok": True, "status": job.status}


@router.post("/api/queue/{job_id}/retry")
def retry_queue_job(job_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    job = retry_job(db, job_id)
    if not job:
        raise HTTPException(404, "Tarefa não encontrada")
    audit(db, "retry_job", f"Tarefa #{job_id} reenfileirada")
    db.commit()
    return {"ok": True, "status": job.status}


@router.post("/api/queue/{job_id}/prioritize")
def prioritize_queue_job(job_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    job = prioritize_job(db, job_id)
    if not job:
        raise HTTPException(404, "Tarefa não encontrada")
    audit(db, "prioritize_job", f"Prioridade da tarefa #{job_id} aumentada")
    db.commit()
    return {"ok": True, "priority": job.priority}


@router.delete("/api/queue/completed")
def clear_completed(owner=Depends(current_owner), db=Depends(get_db)):
    count = clear_completed_jobs(db)
    audit(db, "clear_completed_jobs", f"{count} tarefas concluídas/canceladas removidas")
    db.commit()
    return {"ok": True, "cleared": count}
