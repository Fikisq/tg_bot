"""Точка входа сайта. Запуск: cd front && uvicorn app:app --port 8000 --reload"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers.pages import router as pages_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Домены на починку")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(pages_router)
