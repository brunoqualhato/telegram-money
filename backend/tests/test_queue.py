from app.models import Document, ProcessingJob
from app.services.queue import (
    cancel_job,
    clear_completed_jobs,
    dispatch_queue,
    enqueue_job,
    get_queue_stats,
    prioritize_job,
    retry_job,
)
from app.services.settings import save_settings


def test_enqueue_and_stats(db):
    job1 = enqueue_job(db, category="ai", job_type="ai_document_summary", title="Test 1", target_id="101")
    assert job1.id is not None
    assert job1.status == "pending"

    # Duplicata com mesmo alvo ativo deve retornar a mesma tarefa
    job1_dup = enqueue_job(db, category="ai", job_type="ai_document_summary", title="Test 1 Dup", target_id="101")
    assert job1_dup.id == job1.id

    stats = get_queue_stats(db)
    assert stats["pending"] >= 1
    assert stats["max_ai_concurrency"] == 1
    assert stats["ai_queue_paused"] is False


def test_cancel_retry_and_prioritize(db):
    job = enqueue_job(db, category="ai", job_type="ai_document_summary", title="Test 2", target_id="102")
    job_id = job.id

    # Prioritize
    prioritize_job(db, job_id)
    assert db.get(ProcessingJob, job_id).priority == 10

    # Cancel
    cancel_job(db, job_id)
    assert db.get(ProcessingJob, job_id).status == "cancelled"

    # Retry
    retry_job(db, job_id)
    assert db.get(ProcessingJob, job_id).status == "pending"


def test_clear_completed(db):
    job = enqueue_job(db, category="api", job_type="api_poll", title="Test API")
    cancel_job(db, job.id)
    assert db.get(ProcessingJob, job.id) is not None

    cleared = clear_completed_jobs(db)
    assert cleared >= 1
    assert db.get(ProcessingJob, job.id) is None


def test_ai_concurrency_limit_enforced(db):
    # Configura concorrência máxima de IA como 1
    save_settings(db, {"max_ai_concurrency": "1", "ai_queue_paused": "false"})

    # Cria 2 documentos pendentes
    doc1 = Document(
        ticker="PETR4",
        title="Doc 1",
        kind="fato_relevante",
        source_url="http://example.com/1",
        content_hash="hash1",
        text="PETROBRAS RELATORIO 1",
        status="pending",
    )
    doc2 = Document(
        ticker="VALE3",
        title="Doc 2",
        kind="fato_relevante",
        source_url="http://example.com/2",
        content_hash="hash2",
        text="VALE RELATORIO 2",
        status="pending",
    )
    db.add_all([doc1, doc2])
    db.commit()

    job1 = enqueue_job(db, category="ai", job_type="ai_document_summary", title="Doc 1", target_id=str(doc1.id))
    job2 = enqueue_job(db, category="ai", job_type="ai_document_summary", title="Doc 2", target_id=str(doc2.id))

    # Simula que job1 já está em execução (status = 'running')
    job1.status = "running"
    db.commit()

    # Com slot de IA ocupado (1 rodando, limite 1), dispatch não pode iniciar o job2
    dispatched = dispatch_queue(db)
    assert len(dispatched) == 0

    # O job2 deve permanecer pendente na fila
    assert db.get(ProcessingJob, job2.id).status == "pending"


def test_ai_queue_pause(db):
    save_settings(db, {"ai_queue_paused": "true", "max_ai_concurrency": "1"})
    enqueue_job(db, category="ai", job_type="ai_document_summary", title="Paused Doc", target_id="999")

    dispatched = dispatch_queue(db)
    assert len(dispatched) == 0


def test_queue_api_endpoints(client, owner):
    resp = client.get("/api/queue")
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    assert "settings" in data
    assert "jobs" in data

    # Atualiza configurações de recursos
    settings_payload = {
        "max_ai_concurrency": 2,
        "max_api_concurrency": 5,
        "ai_queue_paused": True,
        "ai_job_timeout_seconds": 180,
        "api_poll_interval_seconds": 60,
    }
    resp = client.post("/api/queue/settings", json=settings_payload)
    assert resp.status_code == 200
    assert resp.json()["settings"]["max_ai_concurrency"] == 2

    # Toggle pause
    resp = client.post("/api/queue/pause")
    assert resp.status_code == 200
    # Como estava True, agora inverte para False
    assert resp.json()["ai_queue_paused"] is False
