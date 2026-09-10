"""Страницы сайта.

Текущий этап — только отображение:
    GET /      -> templates/index.html  (главная, карточки активных тасков)
    GET /admin -> templates/admin.html  (таблица всех тасков, фильтр ?status=)

Задел на будущее (не реализовано, данные пишет внешний скрипт с LLM):
    POST  /api/tasks           {url, sender}        -> создать таск
    PATCH /api/tasks/{id}      {status, message}    -> обновить статус
    GET   /api/tasks?status=…                       -> JSON-список
"""
import asyncio
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from utils import STATUS_LABELS, load_tasks

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _counts(tasks: list[dict]) -> dict:
    return {
        "total": len(tasks),
        "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
        "error": sum(1 for t in tasks if t["status"] == "error"),
        "resolved": sum(1 for t in tasks if t["status"] == "resolved"),
    }


async def _tasks_snapshot() -> list[dict]:
    # чтение файла блокирующее — выносим из цикла событий
    return await asyncio.to_thread(load_tasks)


@router.get("/")
async def index(request: Request):
    tasks = await _tasks_snapshot()
    active = [t for t in tasks if t["status"] in ("in_progress", "error")]
    resolved = [t for t in tasks if t["status"] == "resolved"]
    context = {
        "request": request,
        "active_tasks": active,
        "resolved_tasks": resolved,
        "counts": _counts(tasks),
        "status_labels": STATUS_LABELS,
    }
    return templates.TemplateResponse(request, "index.html", context)


@router.get("/admin")
async def admin(request: Request, status: str | None = None):
    tasks = await _tasks_snapshot()
    if status in STATUS_LABELS:
        tasks = [t for t in tasks if t["status"] == status]
    tasks.sort(key=lambda t: t.get("updated_at", ""), reverse=True)
    context = {
        "request": request,
        "tasks": tasks,
        "counts": _counts(tasks),
        "current_status": status,
        "status_labels": STATUS_LABELS,
    }
    return templates.TemplateResponse(request, "admin.html", context)
