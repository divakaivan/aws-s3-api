FROM python:3.13-slim-bookworm

WORKDIR /app
RUN mkdir -p /app/src/ \
    && touch /app/src/__init__.py
COPY pyproject.toml ./

RUN pip install uvicorn
RUN pip install --editable ./

COPY src/ ./src/

CMD \
    python -c "import boto3; boto3.client('s3').create_bucket(Bucket='$S3_BUCKET_NAME')" \
    && uvicorn files_api.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
