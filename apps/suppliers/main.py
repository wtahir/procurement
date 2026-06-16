from fastapi import FastAPI

from apps.suppliers.rest_harboursteelworks.app import router as rest_supplier_router


def create_app() -> FastAPI:
    app = FastAPI(title="Procura Supplier Mocks", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(
        rest_supplier_router,
        prefix="/rest/harboursteelworks",
        tags=["harboursteelworks"],
    )
    return app


app = create_app()
