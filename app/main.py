from fastapi import FastAPI
from app.services.di.container import get_config_service
# from app.logging import configure_logging
from app.api.v1.routes import router as v1_router

# TODO: enable logging
# configure_logging()
config_svc = get_config_service()

app = FastAPI(title=config_svc.get().app.name, version="0.1.0")
app.include_router(v1_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok", "env": config_svc.get().app.env}
