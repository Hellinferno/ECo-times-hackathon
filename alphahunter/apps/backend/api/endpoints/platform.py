"""Platform API — multi-tenant investment banking workspace layer.

Routers exported by this module (all mounted under /api/platform/ in router.py):
  auth_router        POST /login, GET /me, POST /logout
  companies_router   CRUD for the company registry
  workspaces_router  Research workspace lifecycle + sub-resources
                       (documents, agent runs, tasks, outputs)
  valuations_router  DCF / LBO / Comps run and promotion to output
  outputs_router     Cross-workspace output listing
  macro_router       GET /context — macro overlay for a workspace / symbol

Internal organisation:
  1. Router and constant setup
  2. Shared helpers (response wrapper, coercions, file utils)
  3. DB helpers (company upsert, workspace serialisers, access guard)
  4. Auth endpoints
  5. Company endpoints
  6. Workspace endpoints
  7. Valuation endpoints
  8. Output endpoints
  9. Macro endpoints
"""
from __future__ import annotations

import datetime
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from api.security import (
    CurrentUserDep,
    DbSessionDep,
    ReviewerUserDep,
    authenticate_demo_user,
    create_access_token,
    serialize_user,
)
from models.db import (
    Company,
    Stock,
    Workspace,
    WorkspaceAgentRun,
    WorkspaceDocument,
    WorkspaceOutput,
    WorkspaceTask,
    ValuationRun,
)
from services.macro_service import macro_service
from services.valuation_engine import DeterministicValuationEngine, ValuationContext


# ── Router and constant setup ──────────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["auth"])
companies_router = APIRouter(prefix="/companies", tags=["companies"])
workspaces_router = APIRouter(prefix="/workspaces", tags=["workspaces"])
valuations_router = APIRouter(prefix="/valuations", tags=["valuations"])
outputs_router = APIRouter(prefix="/outputs", tags=["outputs"])
macro_router = APIRouter(prefix="/macro", tags=["macro"])

_engine = DeterministicValuationEngine()
_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_WORKSPACE_UPLOAD_ROOT = _DATA_ROOT / "workspaces"
_WORKSPACE_OUTPUT_ROOT = _DATA_ROOT / "workspace_outputs"
_WORKSPACE_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
_WORKSPACE_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


# ── Shared helpers ─────────────────────────────────────────────────────────────

class WorkspaceNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Workspace not found")


def _ok(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}


def _safe_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _slugify_filename(raw: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() or ch in {".", "_", "-"} else "_" for ch in (raw or "upload"))
    return cleaned.lstrip(".")[:140] or "upload"


def _read_preview(filename: str, blob: bytes) -> tuple[str, str, str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    if ext in {"txt", "md", "json", "csv", "log"}:
        text = blob.decode("utf-8", errors="ignore")[:1500]
        return ext, text, "parsed"
    return ext, "Binary document uploaded successfully. Preview is not available for this file type.", "parsed"


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _ensure_company_for_symbol(db: Session, symbol: str) -> Company:
    normalized = symbol.upper().strip()
    company = db.query(Company).filter(Company.symbol == normalized).first()
    if company:
        return company

    stock = db.query(Stock).filter(Stock.symbol == normalized).first()
    company = Company(
        stock_id=stock.id if stock else None,
        symbol=normalized,
        name=stock.name if stock else normalized,
        sector=stock.sector if stock else None,
        listing_status="listed",
        exchange="NSE",
        country="India",
        market_cap=stock.market_cap_cr if stock else None,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def _ensure_company(db: Session, payload: dict[str, Any]) -> Company:
    symbol = _safe_text(payload.get("symbol"))
    company_id = _safe_text(payload.get("company_id"))
    if company_id:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")
        return company
    if symbol:
        return _ensure_company_for_symbol(db, symbol)

    name = _safe_text(payload.get("name"))
    if not name:
        raise HTTPException(status_code=400, detail="A company name or symbol is required")

    company = Company(
        symbol=symbol.upper() if symbol else None,
        name=name,
        sector=_safe_text(payload.get("sector")),
        listing_status=_safe_text(payload.get("listing_status")) or "private",
        exchange=_safe_text(payload.get("exchange")),
        country=_safe_text(payload.get("country")) or "India",
        market_cap=payload.get("market_cap"),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def _serialize_company(db: Session, company: Company) -> dict[str, Any]:
    workspace_count = db.query(Workspace).filter(Workspace.company_id == company.id).count()
    return {
        "id": company.id,
        "symbol": company.symbol,
        "name": company.name,
        "sector": company.sector,
        "listing_status": company.listing_status,
        "exchange": company.exchange,
        "country": company.country,
        "market_cap": _safe_number(company.market_cap),
        "workspace_count": workspace_count,
    }


def _workspace_counts(db: Session, workspace_id: str) -> dict[str, Any]:
    documents = db.query(WorkspaceDocument).filter(WorkspaceDocument.workspace_id == workspace_id).all()
    tasks = db.query(WorkspaceTask).filter(WorkspaceTask.workspace_id == workspace_id).all()
    outputs = db.query(WorkspaceOutput).filter(WorkspaceOutput.workspace_id == workspace_id).all()
    valuations = db.query(ValuationRun).filter(ValuationRun.workspace_id == workspace_id).all()
    open_tasks = len([task for task in tasks if task.status != "done"])
    latest_valuation = valuations[0] if valuations else None

    return {
        "documents": len(documents),
        "parsed_documents": len([doc for doc in documents if doc.parse_status == "parsed"]),
        "open_tasks": open_tasks,
        "outputs": len(outputs),
        "approved_outputs": len([output for output in outputs if output.review_status == "approved"]),
        "latest_valuation_status": latest_valuation.status if latest_valuation else "idle",
    }


def _serialize_task(task: WorkspaceTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "owner_label": task.owner_label,
        "description": task.description,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "created_at": task.created_at.isoformat(),
    }


def _serialize_document(document: WorkspaceDocument) -> dict[str, Any]:
    return {
        "id": document.id,
        "workspace_id": document.workspace_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "file_size_bytes": document.file_size_bytes,
        "category": document.category,
        "classification": document.classification,
        "parse_status": document.parse_status,
        "rag_status": document.rag_status,
        "text_preview": document.text_preview,
        "uploaded_at": document.uploaded_at.isoformat(),
    }


def _serialize_agent_run(agent_run: WorkspaceAgentRun) -> dict[str, Any]:
    return {
        "id": agent_run.id,
        "workspace_id": agent_run.workspace_id,
        "agent_type": agent_run.agent_type,
        "task_name": agent_run.task_name,
        "status": agent_run.status,
        "parameters": agent_run.parameters_json or {},
        "summary": agent_run.summary,
        "confidence": _safe_number(agent_run.confidence),
        "error_message": agent_run.error_message,
        "created_at": agent_run.created_at.isoformat(),
        "completed_at": agent_run.completed_at.isoformat() if agent_run.completed_at else None,
    }


def _serialize_valuation(valuation: ValuationRun) -> dict[str, Any]:
    result_summary = valuation.result_summary_json or {}
    summary = result_summary.get("summary", {}) if isinstance(result_summary, dict) else {}
    return {
        "id": valuation.id,
        "workspace_id": valuation.workspace_id,
        "model_type": valuation.model_type,
        "status": valuation.status,
        "headline_value": summary.get("headline_value"),
        "headline_metric": summary.get("headline_metric"),
        "warnings": valuation.warnings_json or [],
        "created_at": valuation.created_at.isoformat(),
        "completed_at": valuation.completed_at.isoformat() if valuation.completed_at else None,
        "assumptions": valuation.assumptions_json or {},
        "result_summary": valuation.result_summary_json or {},
    }


def _serialize_output(output: WorkspaceOutput) -> dict[str, Any]:
    return {
        "id": output.id,
        "workspace_id": output.workspace_id,
        "source_run_id": output.source_run_id,
        "source_kind": output.source_kind,
        "output_type": output.output_type,
        "review_status": output.review_status,
        "version": output.version,
        "title": output.title,
        "preview_markdown": output.preview_markdown,
        "created_at": output.created_at.isoformat(),
    }


def _build_workspace_defaults(company: Company, workspace: Workspace) -> dict[str, Any]:
    context = ValuationContext(
        workspace_type=workspace.workspace_type,
        company_name=company.name,
        industry=company.sector or "General",
        current_market_cap=_safe_number(company.market_cap),
        current_price=None,
    )
    return _engine.build_defaults(context)


def _serialize_workspace(db: Session, workspace: Workspace, company: Company | None = None) -> dict[str, Any]:
    company_record = company or db.query(Company).filter(Company.id == workspace.company_id).first()
    counts = _workspace_counts(db, workspace.id)
    return {
        "id": workspace.id,
        "company_id": workspace.company_id,
        "workspace_type": workspace.workspace_type,
        "title": workspace.title,
        "stage": workspace.stage,
        "owner_id": workspace.owner_id,
        "source_symbol": workspace.source_symbol,
        "source_decision_id": workspace.source_decision_id,
        "created_at": workspace.created_at.isoformat(),
        "updated_at": workspace.updated_at.isoformat(),
        "health_summary": counts,
        "notes": workspace.notes,
        "company": _serialize_company(db, company_record) if company_record else None,
    }


def _get_workspace_for_user(db: Session, workspace_id: str, current_user: dict[str, Any]) -> Workspace:
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.org_id == current_user["org_id"])
        .first()
    )
    if workspace is None:
        raise WorkspaceNotFoundError()
    return workspace


def _ensure_default_tasks(db: Session, workspace: Workspace) -> None:
    existing = db.query(WorkspaceTask).filter(WorkspaceTask.workspace_id == workspace.id).count()
    if existing:
        return
    templates = [
        ("Frame the investment thesis", "in_progress", "high"),
        ("Review valuation assumptions", "todo", "high"),
        ("Prepare publishable output", "todo", "medium"),
    ]
    for title, status_value, priority in templates:
        db.add(
            WorkspaceTask(
                workspace_id=workspace.id,
                title=title,
                status=status_value,
                priority=priority,
                owner_label="AI Copilot",
            )
        )
    db.commit()


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@auth_router.post("/login")
async def login(payload: dict[str, Any], db: DbSessionDep):
    username = _safe_text(payload.get("username")) or "analyst"
    password = _safe_text(payload.get("password")) or ""
    org, user = authenticate_demo_user(db, username, password)
    token, expires_at = create_access_token(user, org)
    return _ok({"access_token": token, "expires_at": expires_at, "user": serialize_user(user, org)})


@auth_router.get("/me")
async def me(current_user: CurrentUserDep):
    return _ok({
        "id": current_user["user_id"],
        "org_id": current_user["org_id"],
        "org_slug": current_user["org_slug"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"],
    })


@auth_router.post("/logout")
async def logout(current_user: CurrentUserDep):
    return _ok({"message": f"Session closed for {current_user['username']}"})


# ── Company endpoints ──────────────────────────────────────────────────────────

@companies_router.get("")
async def list_companies(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    q: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = db.query(Company)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter((Company.name.ilike(like)) | (Company.symbol.ilike(like)))
    companies = query.order_by(Company.updated_at.desc()).limit(limit).all()
    return _ok({"companies": [_serialize_company(db, company) for company in companies]})


@companies_router.post("")
async def create_company(payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    company = _ensure_company(db, payload)
    return _ok(_serialize_company(db, company))


# ── Workspace endpoints ────────────────────────────────────────────────────────

@workspaces_router.get("")
async def list_workspaces(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    workspace_type: str | None = Query(default=None),
    stage: str | None = Query(default=None),
):
    query = db.query(Workspace).filter(Workspace.org_id == current_user["org_id"])
    if workspace_type:
        query = query.filter(Workspace.workspace_type == workspace_type)
    if stage:
        query = query.filter(Workspace.stage == stage)
    workspaces = query.order_by(Workspace.updated_at.desc()).all()
    return _ok({"workspaces": [_serialize_workspace(db, workspace) for workspace in workspaces]})


@workspaces_router.post("")
async def create_workspace(payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    company = _ensure_company(db, payload)
    title = _safe_text(payload.get("title")) or f"{company.name} workspace"
    workspace = Workspace(
        org_id=current_user["org_id"],
        owner_id=current_user["user_id"],
        company_id=company.id,
        workspace_type=_safe_text(payload.get("workspace_type")) or ("public_equity" if company.symbol else "private_company"),
        title=title,
        stage=_safe_text(payload.get("stage")) or "active",
        source_symbol=company.symbol,
        source_decision_id=_safe_text(payload.get("source_decision_id")),
        notes=_safe_text(payload.get("notes")),
        health_summary={"status": "warming_up"},
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    _ensure_default_tasks(db, workspace)
    return _ok(_serialize_workspace(db, workspace, company))


@workspaces_router.post("/from-opportunity")
async def create_workspace_from_opportunity(payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    symbol = _safe_text(payload.get("symbol"))
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    company = _ensure_company_for_symbol(db, symbol)
    existing = (
        db.query(Workspace)
        .filter(
            Workspace.org_id == current_user["org_id"],
            Workspace.company_id == company.id,
            Workspace.workspace_type == "public_equity",
        )
        .first()
    )
    if existing:
        return _ok(_serialize_workspace(db, existing, company))

    workspace = Workspace(
        org_id=current_user["org_id"],
        owner_id=current_user["user_id"],
        company_id=company.id,
        workspace_type="public_equity",
        title=_safe_text(payload.get("title")) or f"{company.symbol or company.name} coverage workspace",
        stage="active",
        source_symbol=company.symbol,
        source_decision_id=_safe_text(payload.get("source_decision_id")),
        health_summary={"status": "linked_from_market"},
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    _ensure_default_tasks(db, workspace)
    return _ok(_serialize_workspace(db, workspace, company))


@workspaces_router.get("/{workspace_id}")
async def get_workspace(workspace_id: str, db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    company = db.query(Company).filter(Company.id == workspace.company_id).first()
    documents = (
        db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.workspace_id == workspace.id)
        .order_by(WorkspaceDocument.uploaded_at.desc())
        .all()
    )
    agent_runs = (
        db.query(WorkspaceAgentRun)
        .filter(WorkspaceAgentRun.workspace_id == workspace.id)
        .order_by(WorkspaceAgentRun.created_at.desc())
        .limit(8)
        .all()
    )
    valuations = (
        db.query(ValuationRun)
        .filter(ValuationRun.workspace_id == workspace.id)
        .order_by(ValuationRun.created_at.desc())
        .limit(6)
        .all()
    )
    outputs = (
        db.query(WorkspaceOutput)
        .filter(WorkspaceOutput.workspace_id == workspace.id)
        .order_by(WorkspaceOutput.created_at.desc())
        .limit(8)
        .all()
    )
    tasks = (
        db.query(WorkspaceTask)
        .filter(WorkspaceTask.workspace_id == workspace.id)
        .order_by(WorkspaceTask.created_at.asc())
        .all()
    )

    return _ok({
        "workspace": _serialize_workspace(db, workspace, company),
        "documents": [_serialize_document(document) for document in documents],
        "agent_runs": [_serialize_agent_run(agent_run) for agent_run in agent_runs],
        "valuations": [_serialize_valuation(valuation) for valuation in valuations],
        "outputs": [_serialize_output(output) for output in outputs],
        "tasks": [_serialize_task(task) for task in tasks],
        "default_valuation_inputs": _build_workspace_defaults(company, workspace) if company else {},
    })


@workspaces_router.get("/{workspace_id}/documents")
async def list_workspace_documents(workspace_id: str, db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    documents = (
        db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.workspace_id == workspace.id)
        .order_by(WorkspaceDocument.uploaded_at.desc())
        .all()
    )
    return _ok({"documents": [_serialize_document(document) for document in documents]})


@workspaces_router.post("/{workspace_id}/documents")
async def upload_workspace_documents(
    workspace_id: str,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    files: list[UploadFile] = File(...),
    category: str | None = Form(default=None),
    classification: str | None = Form(default=None),
):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    upload_dir = _WORKSPACE_UPLOAD_ROOT / workspace.id
    upload_dir.mkdir(parents=True, exist_ok=True)
    uploaded: list[dict[str, Any]] = []

    for file in files:
        safe_name = _slugify_filename(file.filename or "upload")
        blob = await file.read()
        file_type, preview, parse_status = _read_preview(safe_name, blob)
        document_id = str(uuid.uuid4())
        destination = upload_dir / f"{document_id}_{safe_name}"
        destination.write_bytes(blob)
        document = WorkspaceDocument(
            id=document_id,
            workspace_id=workspace.id,
            uploaded_by=current_user["user_id"],
            filename=safe_name,
            file_type=file_type,
            file_size_bytes=len(blob),
            category=_safe_text(category),
            classification=_safe_text(classification) or "internal",
            parse_status=parse_status,
            rag_status="indexed",
            storage_path=str(destination),
            text_preview=preview,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        uploaded.append(_serialize_document(document))

    return _ok({"documents": uploaded})


@workspaces_router.get("/{workspace_id}/agents/runs")
async def list_agent_runs(workspace_id: str, db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    runs = (
        db.query(WorkspaceAgentRun)
        .filter(WorkspaceAgentRun.workspace_id == workspace.id)
        .order_by(WorkspaceAgentRun.created_at.desc())
        .all()
    )
    return _ok({"runs": [_serialize_agent_run(agent_run) for agent_run in runs]})


@workspaces_router.post("/{workspace_id}/agents/run")
async def run_agent(workspace_id: str, payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    company = db.query(Company).filter(Company.id == workspace.company_id).first()
    macro_context = macro_service.get_context(symbol=company.symbol if company else None, sector=company.sector if company else None)
    agent_type = _safe_text(payload.get("agent_type")) or "research"
    task_name = _safe_text(payload.get("task_name")) or "research_brief"
    prompt = _safe_text(payload.get("prompt")) or "Create a concise research brief."
    summary = (
        f"{agent_type.title()} agent ran '{task_name}' for {company.name if company else workspace.title}. "
        f"Prompt: {prompt} Market regime: {macro_context['market_regime']}."
    )
    confidence = 0.72 if workspace.workspace_type == "public_equity" else 0.78
    agent_run = WorkspaceAgentRun(
        workspace_id=workspace.id,
        requested_by=current_user["user_id"],
        agent_type=agent_type,
        task_name=task_name,
        status="completed",
        parameters_json={
            "prompt": prompt,
            "parameters": payload.get("parameters") or {},
            "macro_context": macro_context,
        },
        summary=summary,
        confidence=confidence,
        completed_at=datetime.datetime.utcnow(),
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)
    return _ok(_serialize_agent_run(agent_run))


@workspaces_router.get("/{workspace_id}/tasks")
async def list_tasks(workspace_id: str, db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    tasks = (
        db.query(WorkspaceTask)
        .filter(WorkspaceTask.workspace_id == workspace.id)
        .order_by(WorkspaceTask.created_at.asc())
        .all()
    )
    return _ok({"tasks": [_serialize_task(task) for task in tasks]})


@workspaces_router.post("/{workspace_id}/tasks")
async def create_task(workspace_id: str, payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    title = _safe_text(payload.get("title"))
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    task = WorkspaceTask(
        workspace_id=workspace.id,
        title=title,
        status=_safe_text(payload.get("status")) or "todo",
        priority=_safe_text(payload.get("priority")) or "medium",
        owner_label=_safe_text(payload.get("owner_label")) or "Team",
        description=_safe_text(payload.get("description")),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _ok(_serialize_task(task))


@workspaces_router.patch("/{workspace_id}/tasks/{task_id}")
async def update_task(workspace_id: str, task_id: str, payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    task = (
        db.query(WorkspaceTask)
        .filter(WorkspaceTask.workspace_id == workspace.id, WorkspaceTask.id == task_id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if _safe_text(payload.get("status")):
        task.status = _safe_text(payload.get("status")) or task.status
    if _safe_text(payload.get("priority")):
        task.priority = _safe_text(payload.get("priority")) or task.priority
    if _safe_text(payload.get("description")):
        task.description = _safe_text(payload.get("description"))
    db.commit()
    db.refresh(task)
    return _ok(_serialize_task(task))


# ── Valuation endpoints ────────────────────────────────────────────────────────

@valuations_router.get("")
async def list_valuations(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    workspace_id: str | None = Query(default=None),
):
    query = db.query(ValuationRun).join(Workspace, Workspace.id == ValuationRun.workspace_id).filter(Workspace.org_id == current_user["org_id"])
    if workspace_id:
        query = query.filter(ValuationRun.workspace_id == workspace_id)
    valuations = query.order_by(ValuationRun.created_at.desc()).all()
    return _ok({"valuations": [_serialize_valuation(valuation) for valuation in valuations]})


@valuations_router.post("/run")
async def run_valuation(payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    workspace_id = _safe_text(payload.get("workspace_id"))
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    company = db.query(Company).filter(Company.id == workspace.company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    context = ValuationContext(
        workspace_type=workspace.workspace_type,
        company_name=company.name,
        industry=company.sector or "General",
        current_market_cap=_safe_number(company.market_cap),
        current_price=None,
    )
    result = _engine.run(_safe_text(payload.get("model_type")) or "dcf", payload.get("assumptions") or {}, context)
    valuation = ValuationRun(
        workspace_id=workspace.id,
        requested_by=current_user["user_id"],
        model_type=result["model_type"],
        status=result["status"],
        assumptions_json=result["inputs"],
        result_summary_json=result,
        warnings_json=result.get("warnings") or [],
        completed_at=datetime.datetime.utcnow(),
    )
    db.add(valuation)
    db.commit()
    db.refresh(valuation)
    return _ok(_serialize_valuation(valuation))


@valuations_router.get("/{valuation_id}")
async def get_valuation(valuation_id: str, db: DbSessionDep, current_user: CurrentUserDep):
    valuation = (
        db.query(ValuationRun)
        .join(Workspace, Workspace.id == ValuationRun.workspace_id)
        .filter(ValuationRun.id == valuation_id, Workspace.org_id == current_user["org_id"])
        .first()
    )
    if valuation is None:
        raise HTTPException(status_code=404, detail="Valuation not found")
    return _ok(_serialize_valuation(valuation))


@valuations_router.post("/{valuation_id}/promote")
async def promote_valuation(valuation_id: str, payload: dict[str, Any], db: DbSessionDep, current_user: CurrentUserDep):
    valuation = (
        db.query(ValuationRun)
        .join(Workspace, Workspace.id == ValuationRun.workspace_id)
        .filter(ValuationRun.id == valuation_id, Workspace.org_id == current_user["org_id"])
        .first()
    )
    if valuation is None:
        raise HTTPException(status_code=404, detail="Valuation not found")
    workspace = db.query(Workspace).filter(Workspace.id == valuation.workspace_id).first()
    company = db.query(Company).filter(Company.id == workspace.company_id).first() if workspace else None
    valuation_result = valuation.result_summary_json or {}
    summary = valuation_result.get("summary", {}) if isinstance(valuation_result, dict) else {}
    title = _safe_text(payload.get("title")) or f"{company.name if company else 'Workspace'} investment memo"
    preview_markdown = "\n".join([
        f"# {title}",
        "",
        f"- Workspace: {workspace.title if workspace else valuation.workspace_id}",
        f"- Model: {valuation.model_type.upper()}",
        f"- Headline: {summary.get('headline_metric', 'Valuation result')} = {summary.get('headline_value')}",
        f"- Confidence band: {summary.get('confidence_band', 'Working draft')}",
        "",
        "## Notes",
        "This memo was promoted from the valuation lab. Review and approve before external use.",
    ])
    output = WorkspaceOutput(
        workspace_id=valuation.workspace_id,
        source_run_id=valuation.id,
        source_kind="valuation",
        output_type=_safe_text(payload.get("output_type")) or "investment_memo",
        review_status="draft",
        version=1,
        title=title,
        preview_markdown=preview_markdown,
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return _ok(_serialize_output(output))


# ── Output endpoints ───────────────────────────────────────────────────────────

@outputs_router.get("")
async def list_outputs(db: DbSessionDep, current_user: CurrentUserDep):
    outputs = (
        db.query(WorkspaceOutput)
        .join(Workspace, Workspace.id == WorkspaceOutput.workspace_id)
        .filter(Workspace.org_id == current_user["org_id"])
        .order_by(WorkspaceOutput.created_at.desc())
        .all()
    )
    return _ok({"outputs": [_serialize_output(output) for output in outputs]})


@workspaces_router.get("/{workspace_id}/outputs")
async def list_workspace_outputs(workspace_id: str, db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    outputs = (
        db.query(WorkspaceOutput)
        .filter(WorkspaceOutput.workspace_id == workspace.id)
        .order_by(WorkspaceOutput.created_at.desc())
        .all()
    )
    return _ok({"outputs": [_serialize_output(output) for output in outputs]})


@workspaces_router.patch("/{workspace_id}/outputs/{output_id}/review")
async def review_output(workspace_id: str, output_id: str, payload: dict[str, Any], db: DbSessionDep, current_user: ReviewerUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    output = (
        db.query(WorkspaceOutput)
        .filter(WorkspaceOutput.workspace_id == workspace.id, WorkspaceOutput.id == output_id)
        .first()
    )
    if output is None:
        raise HTTPException(status_code=404, detail="Output not found")
    output.review_status = _safe_text(payload.get("review_status")) or output.review_status
    db.commit()
    db.refresh(output)
    return _ok(_serialize_output(output))


@workspaces_router.get("/{workspace_id}/outputs/{output_id}/download")
async def download_output(workspace_id: str, output_id: str, db: DbSessionDep, current_user: CurrentUserDep):
    workspace = _get_workspace_for_user(db, workspace_id, current_user)
    output = (
        db.query(WorkspaceOutput)
        .filter(WorkspaceOutput.workspace_id == workspace.id, WorkspaceOutput.id == output_id)
        .first()
    )
    if output is None:
        raise HTTPException(status_code=404, detail="Output not found")
    if output.review_status != "approved":
        raise HTTPException(status_code=409, detail="Output must be approved before download")
    return PlainTextResponse(output.preview_markdown or "No preview available.", media_type="text/markdown")


# ── Macro endpoints ────────────────────────────────────────────────────────────

@macro_router.get("/context")
async def get_macro_context(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    workspace_id: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
    sector: str | None = Query(default=None),
):
    resolved_symbol = _safe_text(symbol)
    resolved_sector = _safe_text(sector)

    if workspace_id:
        workspace = _get_workspace_for_user(db, workspace_id, current_user)
        company = db.query(Company).filter(Company.id == workspace.company_id).first()
        if company:
            resolved_symbol = resolved_symbol or company.symbol
            resolved_sector = resolved_sector or company.sector

    return _ok(macro_service.get_context(symbol=resolved_symbol, sector=resolved_sector))
