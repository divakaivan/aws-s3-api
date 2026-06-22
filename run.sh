#!/usr/bin/env bash

set -e

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
AWS_LAMBDA_FUNCTION_NAME="files-api-handler"
BUILD_DIR_REL_PATH="./build"
BUILD_DIR="${THIS_DIR}/${BUILD_DIR_REL_PATH}"

function run {
    PYTHONPATH=src uv run uvicorn files_api.main:create_app --reload
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

    export LOGURU_LEVEL="DEBUG"
    PYTHONPATH=src uv run uvicorn files_api.main:create_app --reload
    wait $MOTO_PID
}

function lint {
    uv run pre-commit run --all-files
}

function deploy-lambda {
    export AWS_PROFILE=mlops-club
    export AWS_REGION=eu-west-1
    deploy-lambda:cd
}

function deploy-lambda:cd {
    # Get the current user ID and group ID to run the docker command with so that
    # the generated lambda-env folder doesn't have root permissions, instead user level permission
    # This will help in library installation in the docker container and cleaning up the lambda-env folder later on.
    USER_ID=$(id -u)
    GROUP_ID=$(id -g)

    LAMBDA_LAYER_DIR_NAME="lambda-env"
    LAMBDA_LAYER_DIR="${BUILD_DIR}/${LAMBDA_LAYER_DIR_NAME}"
    LAMBDA_LAYER_ZIP_FPATH="${BUILD_DIR}/lambda-layer.zip"
    LAMBDA_HANDLER_ZIP_FPATH="${BUILD_DIR}/lambda.zip"
    SRC_DIR="${THIS_DIR}/src"

    # clean up artifacts
    rm -rf "$LAMBDA_LAYER_DIR" || true
    rm -f "$LAMBDA_LAYER_ZIP_FPATH" || true

    # install dependencies
    docker logout || true # log out to use the public ecr
    docker pull public.ecr.aws/lambda/python:3.13-arm64

    # install dependencies in a docker container to ensure compatibility with AWS Lambda
    #
    # Note: we remote boto3 and botocore because AWS lambda automatically
    # provides these. This saves us ~24MB in the final, uncompressed layer size.
    docker run --rm \
        --user $USER_ID:$GROUP_ID \
        --volume "${THIS_DIR}":/out \
        --entrypoint /bin/bash \
        public.ecr.aws/lambda/python:3.13-arm64 \
        -c " \
        pip install --root --upgrade pip \
        && pip install \
            --editable /out/[aws-lambda] \
            --target /out/${BUILD_DIR_REL_PATH}/${LAMBDA_LAYER_DIR_NAME}/python \
        && rm -rf /out/${BUILD_DIR_REL_PATH}/${LAMBDA_LAYER_DIR_NAME}/python/boto3 \
        && rm -rf /out/${BUILD_DIR_REL_PATH}/${LAMBDA_LAYER_DIR_NAME}/python/botocore \
        "

    # bundle dependencies and handler in a zip file
    cd "$LAMBDA_LAYER_DIR"
    zip -r "$LAMBDA_LAYER_ZIP_FPATH" ./

    cd "$SRC_DIR"
    zip -r "$LAMBDA_HANDLER_ZIP_FPATH" ./

    cd "$THIS_DIR"

    # publish the lambda "deployment package" (the handler)
    aws lambda update-function-code \
        --function-name "$AWS_LAMBDA_FUNCTION_NAME" \
        --zip-file fileb://${LAMBDA_HANDLER_ZIP_FPATH} \
        --output json | cat

    # publish the lambda layer with a new version
    LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
        --layer-name cloud-course-project-python-deps \
        --compatible-runtimes python3.13 \
        --zip-file fileb://${LAMBDA_LAYER_ZIP_FPATH} \
        --compatible-architectures arm64 \
        --query 'LayerVersionArn' \
        --output text | cat)

    # update the lambda function to use the new layer version
    aws lambda update-function-configuration \
        --function-name "$AWS_LAMBDA_FUNCTION_NAME" \
        --layers $LAYER_VERSION_ARN \
        --handler "files_api.aws_lambda_handler.handler" \
        --output json | cat
}

function clean {
    rm -rf dist build coverage.xml test-reports
    find . \
        -type d \
        \( \
        -name "*cache*" \
        -o -name "*.dist-info" \
        -o -name "*.egg-info" \
        -o -name "*htmlcov" \
        \) \
        -not -path "*env/*" \
        -exec rm -r {} + || true

    find . \
        -type f \
        -name "*.pyc" \
        -o -name "*.zip" \
        -o -name "*.DS_Store" \
        -not -path "*env/*" \
        -exec rm {} +
}

function set-local-aws-env-vars {
    export AWS_PROFILE=mlops-club
    export AWS_REGION=eu-west-1
}

function run-locust {
    set-local-aws-env-vars
    aws configure export-credentials --profile $AWS_PROFILE --format env >.env
    docker compose \
        --file docker-compose.yaml \
        --file docker-compose.locust.yaml \
        up \
        --build
}

function run-docker {
    set-local-aws-env-vars
    aws configure export-credentials --profile $AWS_PROFILE --format env >.env
    docker compose up --build
}

function help {
    echo "$0 <task> <args>"
    echo "Tasks:"
    compgen -A function | cat -n
}

"$@"
