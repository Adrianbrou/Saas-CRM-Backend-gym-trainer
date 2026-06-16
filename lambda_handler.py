"""
lambda_handler.py - AWS Lambda entry point (ASGI adapter via Mangum)

The SAME FastAPI app that runs under uvicorn on ECS Fargate runs unchanged on AWS
Lambda behind API Gateway. Mangum is the adapter: it translates the API Gateway /
ALB / Function URL event into the ASGI scope FastAPI expects, drives the app, then
translates the ASGI response back into the {statusCode, headers, body} shape API
Gateway returns to the caller.

Lambda calls `lambda_handler.handler` (module.attribute) as its entry point.

Run it locally two ways:
  - simulate_lambda.py        - invoke this handler with a synthetic event (no AWS, no Docker)
  - `sam local start-api`     - run it behind a real local API Gateway (see template.yaml)

lifespan="off": this app registers no Starlette startup/shutdown handlers, and the
Lambda freeze/thaw model does not map cleanly onto ASGI lifespan, so we disable it.
"""

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
