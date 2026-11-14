from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from ..auth import current_owner
from ..config import settings
from ..crud import rows
from ..db import get_db
from ..models import Document
from ..schemas import DocumentInput
from ..services.documents import save_document

router = APIRouter(tags=["documents"])


@router.get("/api/documents")
def documents(owner=Depends(current_owner), db=Depends(get_db)):
    return jsonable_encoder(
        [
            {key: value for key, value in row.__dict__.items() if key not in ("text", "_sa_instance_state")}
            for row in rows(db, Document, 100)
        ]
    )


@router.post("/api/documents", status_code=201)
def add_document(data: DocumentInput, owner=Depends(current_owner), db=Depends(get_db)):
    row = save_document(db, data)
    return {"id": row.id, "status": row.status}


@router.post("/api/documents/pdf", status_code=201)
def upload_pdf(
    ticker: str = Form(...),
    title: str = Form(...),
    source_url: str = Form(...),
    file: UploadFile = File(...),
    owner=Depends(current_owner),
    db=Depends(get_db),
):
    raw = file.file.read(10_000_001)
    if len(raw) > 10_000_000:
        raise HTTPException(413, "Limite de 10 MB por PDF")
    try:
        import pymupdf

        with pymupdf.open(stream=raw, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise ValueError("PDF protegido")
            incomplete = len(pdf) > 80
            extracted = "\n".join(pdf[i].get_text() for i in range(min(80, len(pdf))))
            incomplete = incomplete or len(extracted) > 200_000
        data = DocumentInput(
            ticker=ticker.upper(),
            title=title,
            source_url=source_url,
            text=extracted[:200_000],
            incomplete=incomplete,
        )
    except Exception:
        raise HTTPException(
            422,
            "PDF inválido, protegido ou sem texto suficiente. PDFs digitalizados precisam de OCR externo.",
        )
    row = save_document(db, data)
    return {"id": row.id, "status": row.status, "incomplete": row.incomplete}


@router.post("/api/documents/{document_id}/summarize")
def retry_summary(document_id: int, owner=Depends(current_owner), db=Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Documento não encontrado")
    if not settings().ai_model:
        model_var = "LM_STUDIO_MODEL" if settings().ai_provider == "lmstudio" else "OLLAMA_MODEL"
        raise HTTPException(503, f"Configure {model_var} para gerar resumos com IA local")
    if document.status == "ready":
        return {"ok": True}
    document.status, document.error = "pending", None
    db.commit()
    return {"ok": True}


@router.post("/api/news/refresh")
def refresh_news(owner=Depends(current_owner), db=Depends(get_db)):
    from ..services.providers import collect_news

    count = collect_news(db)
    return {"message": f"Busca de notícias concluída: {count} novas notícias adicionadas.", "count": count}
