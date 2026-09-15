"""Aggregates all v1 route modules under a single router."""
from fastapi import APIRouter

from app.api.v1.routes import auth, companies, health, me, opportunities, resumes, saved

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(opportunities.router)
api_router.include_router(companies.router)
api_router.include_router(saved.router)
api_router.include_router(resumes.router)
