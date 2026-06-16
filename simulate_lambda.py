"""
simulate_lambda.py - Invoke the Lambda handler locally with synthetic API Gateway events.

Proves the EXACT same FastAPI app runs as an AWS Lambda function behind API Gateway -
no Docker, no SAM, no AWS account. It builds the API Gateway HTTP API (payload v2.0)
event that Lambda would receive, calls the handler, and prints the {statusCode, body}
Lambda would return.

Run:
    .venv\\Scripts\\python.exe simulate_lambda.py
"""

import json

from lambda_handler import handler


class LambdaContext:
    """Minimal stand-in for the AWS Lambda context object passed as the 2nd arg."""

    function_name = "gym-crm"
    memory_limit_in_mb = 512
    invoked_function_arn = "arn:aws:lambda:us-east-1:000000000000:function:gym-crm"
    aws_request_id = "local-sim-request-id"

    def get_remaining_time_in_millis(self) -> int:
        return 30000


def apigw_v2_event(method: str, path: str, body=None) -> dict:
    """Build an API Gateway HTTP API (payload format version 2.0) event."""
    raw_body = json.dumps(body) if body is not None else None
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {
            "host": "gym-crm.execute-api.us-east-1.amazonaws.com",
            "content-type": "application/json",
        },
        "requestContext": {
            "accountId": "000000000000",
            "apiId": "gymcrmapi",
            "domainName": "gym-crm.execute-api.us-east-1.amazonaws.com",
            "http": {
                "method": method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "simulate-lambda",
            },
            "requestId": "local-sim-request-id",
            "routeKey": f"{method} {path}",
            "stage": "$default",
            "time": "01/Jan/2026:00:00:00 +0000",
            "timeEpoch": 1767225600000,
        },
        "body": raw_body,
        "isBase64Encoded": False,
    }


def invoke(label: str, method: str, path: str, body=None) -> None:
    print(f"\n=== {label}: {method} {path} ===")
    event = apigw_v2_event(method, path, body)
    response = handler(event, LambdaContext())
    print(f"  statusCode: {response['statusCode']}")
    payload = response.get("body", "")
    try:
        payload = json.dumps(json.loads(payload), indent=2)
    except Exception:
        payload = str(payload)
    # keep the console readable
    if len(payload) > 700:
        payload = payload[:700] + "\n  ... (truncated)"
    for line in payload.splitlines():
        print(f"  {line}")


if __name__ == "__main__":
    print("Invoking the Gym CRM FastAPI app AS AN AWS LAMBDA (via Mangum)")
    print("=" * 62)
    # /health and /openapi.json need no database, so they run with RDS offline.
    invoke("Health check", "GET", "/health")
    invoke("OpenAPI schema (proves the full router is wired)", "GET", "/openapi.json")
    invoke("Unknown route (404 flows through cleanly)", "GET", "/does-not-exist")
    print("\n" + "=" * 62)
    print("Same `app` object FastAPI serves under uvicorn on Fargate.")
    print("No web server was started - this is exactly the Lambda invocation path.")
