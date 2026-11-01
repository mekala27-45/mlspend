"""Vercel entry point for the API and the working dashboard."""

from fastapi.staticfiles import StaticFiles

from packages.api.app import app
from packages.core.io import ROOT

app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="dashboard")
