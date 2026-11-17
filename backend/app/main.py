"""VEGA DEFENCE INTELLIGENCE — Sovereign Defence Intelligence & Decision Support Platform (API)."""
import time, logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
import os

from .db import Base, engine, SessionLocal
from .config import get_settings
from .routers import auth, orgs, datasets, entities, cases, search, geo, ai, ops, admin, access

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
log = logging.getLogger("gotham")
settings = get_settings()

app = FastAPI(
    title="VEGA DEFENCE API",
    version="1.0.0",
    description="Sovereign defence intelligence and operational decision-support platform. All demonstration data is synthetic.",
    docs_url="/api/docs", openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)

@app.middleware("http")
async def observability_and_limits(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{dur:.1f}"
    log.info(f'{request.method} {request.url.path} {response.status_code} {dur:.1f}ms')
    return response

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse({"detail": "Validation error", "errors": exc.errors()}, status_code=422)

for r in (auth, orgs, datasets, entities, cases, search, geo, ai, ops, admin, access):
    app.include_router(r.router)

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "gotham-india-api", "version": "1.0.0"}

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    if settings.SEED_DEMO:
        db = SessionLocal()
        try:
            from .seed import seed
            log.info(f"seed: {seed(db)}")
        finally:
            db.close()

# Serve the built single-page client if present (production single-origin deployment with SPA routing)
from fastapi.responses import FileResponse

DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.isdir(DIST):
    assets_dir = os.path.join(DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST, "index.html"))
