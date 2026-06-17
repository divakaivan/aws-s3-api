#!/usr/bin/env bash

set -e

function run {
    uv run uvicorn src.files_api.main:create_app --reload
}

function run-mock {
    set +e

    uv run moto_server -p 5000 &
    MOTO_PID=$!

    unset AWS_PROFILE
    export AWS_ENDPOINT_URL="http://127.0.0.1:5000"
    export AWS_SECRET_ACCESS_KEY="mock"
    export AWS_ACCESS_KEY_ID="mock"
    export AWS_REGION="us-east-1"
    export S3_BUCKET_NAME="some-bucket"

    aws --endpoint-url "$AWS_ENDPOINT_URL" s3 mb "s3://$S3_BUCKET_NAME"
    trap 'kill $MOTO_PID' EXIT

    uv run uvicorn src.files_api.main:create_app --reload
    wait $MOTO_PID
}

"$@"
