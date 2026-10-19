import json

from fastapi.testclient import TestClient

import app as curriculum


def test_tutor_requires_server_side_groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")
    client = TestClient(curriculum.app)
    response = client.post("/tutor/chat", json={
        "board": "CBSE",
        "class_level": 6,
        "subject": "Science",
        "medium": "English",
        "app_language": "Tanglish",
        "message": "Explain photosynthesis simply.",
    })
    assert response.status_code == 503
    assert "not ready" in response.json()["detail"].lower()


def test_tutor_uses_profile_and_gentle_prompt(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "Namma simple-a paakalam. Plants use sunlight to make food."}}]
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = request.headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    client = TestClient(curriculum.app)
    response = client.post("/tutor/chat", json={
        "board": "CBSE",
        "class_level": 6,
        "subject": "Science",
        "medium": "English",
        "app_language": "Tanglish",
        "student_name": "Test learner",
        "message": "Explain photosynthesis simply.",
        "history": [{"role": "user", "content": "I am confused."}],
    })
    assert response.status_code == 200
    assert response.json()["answer"].startswith("Namma")
    assert response.json()["grounded"] is False
    assert captured["payload"]["model"] == "openai/gpt-oss-20b"
    assert "Never shame" in captured["payload"]["messages"][0]["content"]
    assert "Tanglish" in captured["payload"]["messages"][0]["content"]
    assert captured["timeout"] == 30

def test_tutor_speech_requires_server_side_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = TestClient(curriculum.app)
    response = client.post("/tutor/speech", json={
        "text": "Let's learn this one small step at a time.",
        "app_language": "English",
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_tutor_speech_returns_wav_and_uses_gentle_voice(monkeypatch):
    import base64
    import io
    import wave

    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            pcm = b"\\x00\\x00" * 24
            return json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{
                            "inlineData": {
                                "mimeType": "audio/L16;rate=24000",
                                "data": base64.b64encode(pcm).decode("ascii"),
                            }
                        }]
                    }
                }]
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = request.headers
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    client = TestClient(curriculum.app)
    response = client.post("/tutor/speech", json={
        "text": "Namma idha simple-a paakalam.",
        "app_language": "Tanglish",
    })
    assert response.status_code == 200
    body = response.json()
    wav_bytes = base64.b64decode(body["audio_base64"])
    with wave.open(io.BytesIO(wav_bytes), "rb") as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getframerate() == 24000
        assert audio.readframes(24) == b"\\x00\\x00" * 24
    assert body["provider"] == "gemini"
    assert captured["headers"]["X-goog-api-key"] == "test-gemini-key"
    assert captured["payload"]["generationConfig"]["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voice"] == "Aoede"
    assert "Tanglish" in captured["payload"]["contents"][0]["parts"][0]["text"]

def test_voice_health_reports_configuration_without_secret(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-returned")
    response = TestClient(curriculum.app).get("/health/voice")
    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert response.json()["provider"] == "gemini"
    assert "must-not-be-returned" not in response.text

