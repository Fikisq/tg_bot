import json
import logging
from pathlib import Path
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TASKS_FILE = BASE_DIR / "data" / "tasks.json"


def to_domain(raw: str) -> str:
    """Нормализует ссылку до домена: https://www.amd.com/ru?x=1 -> www.amd.com"""
    raw = raw.strip()
    if "://" not in raw:
        raw = "//" + raw
    netloc = urlsplit(raw).netloc
    host = netloc.split("@")[-1].split(":")[0]  # убрать user:pass@ и :port
    return host.lower()


def load_tasks() -> list[dict]:
    """Читает data/tasks.json при каждом запросе: файл обновляют внешние компоненты."""
    try:
        with open(TASKS_FILE, "r", encoding="UTF-8") as f:
            tasks = json.load(f)
    except FileNotFoundError:
        logger.warning("Файл %s не найден", TASKS_FILE)
        return []
    except json.JSONDecodeError as error:
        logger.warning("Файл %s битый: %s", TASKS_FILE, error)
        return []

    for task in tasks:
        if not task.get("domain"):
            task["domain"] = to_domain(task.get("url", ""))
    return tasks


STATUS_LABELS = {
    "in_progress": "В работе",
    "error": "Ошибка",
    "resolved": "Решено",
}
