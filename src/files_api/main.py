from fastapi import FastAPI
from src.files_api.routes import ROUTER
from src.files_api.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(
        title="Files API",
        description="A simple API to manage files in S3",
    )
    app.state.settings = settings
    app.include_router(ROUTER)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
