from fastapi import FastAPI

from apps.suppliers.rest_alrajhi.app import router as alrajhi_router


def create_app() -> FastAPI:
    app = FastAPI(title="Procura Supplier Mocks", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(alrajhi_router, prefix="/rest/alrajhi", tags=["alrajhi"])
    return app


app = create_app()
