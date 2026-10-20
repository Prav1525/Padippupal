import io
import os
import threading
from typing import Optional

import numpy as np
import soundfile as sf
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

app = FastAPI(title="PadippuPal Kokoro TTS", version="0.1.0")

# Load once per process. CPU inference is intentional for a free-tier prototype.
_pipeline = None
_pipeline_lock = threading.Lock()
ALLOWED_VOICES = {"af_heart", "af_bella", "af_nicole", "af_sarah", "am_adam", "am_michael"}
API_TOKEN = os.getenv("TTS_API_TOKEN", "").strip()


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1800)
    voice: str = "af_heart"
    speed: float = Field(default=1.0, ge=0.7, le=1.3)


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                from kokoro import KPipeline
                _pipeline = KPipeline(lang_code="a")
    return _pipeline


@app.get("/")
def root():
    return {"service": "PadippuPal Kokoro TTS", "status": "ready", "auth_required": bool(API_TOKEN)}


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _pipeline is not None}


@app.post("/tts")
def tts(body: TTSRequest, authorization: Optional[str] = Header(default=None)):
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="Server is not configured: set TTS_API_TOKEN.")
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token.")
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Text must not be blank.")
    if body.voice not in ALLOWED_VOICES:
        raise HTTPException(status_code=422, detail=f"Unsupported voice. Choose one of: {', '.join(sorted(ALLOWED_VOICES))}.")

    try:
        pipeline = get_pipeline()
        chunks = []
        # Serialise model inference to avoid concurrent CPU memory spikes.
        with _pipeline_lock:
            for _, _, audio in pipeline(text, voice=body.voice, speed=body.speed):
                if audio is not None and len(audio):
                    chunks.append(np.asarray(audio, dtype=np.float32))
        if not chunks:
            raise HTTPException(status_code=500, detail="Kokoro produced no audio.")
        audio = np.concatenate(chunks)
        wav = io.BytesIO()
        sf.write(wav, audio, 24000, format="WAV", subtype="PCM_16")
        return Response(content=wav.getvalue(), media_type="audio/wav",
                        headers={"Cache-Control": "no-store", "X-Audio-Sample-Rate": "24000"})
    except HTTPException:
        raise
    except Exception as exc:
        # Do not expose internal stack traces or secrets in API responses.
        raise HTTPException(status_code=500, detail=f"TTS generation failed ({type(exc).__name__}).") from exc
