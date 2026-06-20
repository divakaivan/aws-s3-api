import json
from pathlib import Path

from fastapi.openapi.utils import get_openapi

from src.files_api.main import create_app
from src.files_api.settings import Settings

OUTPUT_SPEC = Path("openapi.json")


def main() -> None:
    generated_openapi_schema = generate_openapi()
    write_openapi_to_disk(openapi_schema=generated_openapi_schema)
    print("✅ Wrote OpenAPI schema to disk.")


def generate_openapi() -> dict:
    """
    Generate the OpenAPI schema for the FastAPI application.

    Official docs for generating the FastAPI schema:
    https://fastapi.tiangolo.com/how-to/extending-openapi/?h=get_open#generate-the-openapi-schema
    """
    settings = Settings(s3_bucket_name="placeholder")
    app = create_app(settings=settings)
    return get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        summary=app.summary,
        description=app.description,
        tags=app.openapi_tags,
        servers=app.servers,
        license_info=app.license_info,
        contact=app.contact,
        terms_of_service=app.terms_of_service,
        routes=app.routes,
    )


def write_openapi_to_disk(openapi_schema: dict) -> None:
    OUTPUT_SPEC.write_text(json.dumps(openapi_schema, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
