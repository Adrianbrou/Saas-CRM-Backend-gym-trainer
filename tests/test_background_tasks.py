"""
test_background_tasks.py - proves the welcome email is dispatched as a background task.

FastAPI runs BackgroundTasks AFTER the response is returned. TestClient executes them
synchronously, so once the POST returns we can assert the task fired. We patch the email
function so no real SMTP is attempted - we only care that the task was scheduled and ran.
"""


def test_welcome_email_dispatched_on_member_create(auth_client, monkeypatch):
    import app.api.members as members

    calls = []
    monkeypatch.setattr(members, "send_welcome_email",
                        lambda *args, **kwargs: calls.append(args))

    response = auth_client.post("/members/", json={
        "name": "BG Tester",
        "email": "bg@test.com",
        "phone": "5551234",
        "gym_id": 1,
    })

    assert response.status_code == 201
    # The background task ran after the response and called our patched email function once.
    assert len(calls) == 1
    assert calls[0][0] == "bg@test.com"  # first positional arg is the recipient email
