"""FastAPI server for the Cerberus web dashboard."""

from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from cerberus_api import CerberusAPI

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "docs"

app = FastAPI(title="Cerberus Command Center")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = CerberusAPI()


@app.get("/api/dashboard")
def dashboard():
    return api.get_dashboard_stats()


@app.get("/api/clients")
def clients():
    return api.get_clients()


@app.get("/api/jobs")
def jobs():
    return api.get_jobs()


@app.get("/api/leads")
def leads():
    return api.get_leads()


@app.get("/api/agents")
def agents():
    return api.get_agents()


@app.get("/api/notes")
def notes():
    return api.get_notes()


@app.get("/api/transactions")
def transactions(limit: int = 50):
    return api.get_transactions(limit=limit)


@app.get("/api/revenue")
def revenue(days: int = 30):
    return api.get_revenue_chart(days=days)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
