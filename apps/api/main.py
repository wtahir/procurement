from fastapi import FastAPI

from apps.api.errors import register_error_handlers
from apps.api.routes.approvals import router as approvals_router
from apps.api.routes.health import router as health_router
from apps.api.routes.orders import router as orders_router
from apps.api.routes.stream import router as stream_router
from apps.api.routes.voice import router as voice_router
from apps.api.routes.webhooks import router as webhooks_router
from apps.api.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Procura API", version="0.1.0", debug=settings.app_env == "development")
    register_error_handlers(app)
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(orders_router, prefix="/orders", tags=["orders"])
    app.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
    app.include_router(voice_router, prefix="/voice", tags=["voice"])
    app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(stream_router, prefix="/stream", tags=["stream"])
    return app


app = create_app()
