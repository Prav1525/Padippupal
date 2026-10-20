import io
from fastapi.responses import HTMLResponse
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


@app.get("/demo", response_class=HTMLResponse)
def demo():
    # The token is entered by the tester and kept only in this page's memory.
    # It is never stored in localStorage or sent anywhere except this same API.
    return HTMLResponse(r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PadippuPal Voice Lab</title>
<style>
:root{color-scheme:light dark;font-family:system-ui,-apple-system,sans-serif}
body{margin:0;background:#101827;color:#f4f6fb}
main{max-width:720px;margin:auto;padding:24px 16px 48px}
h1{margin-bottom:4px} .sub{color:#b9c4d8;margin-top:0}
.panel{background:#1b273a;border:1px solid #34435c;border-radius:16px;padding:16px;margin:16px 0}
label{display:block;font-weight:600;margin:12px 0 6px}
input,textarea,select{box-sizing:border-box;width:100%;padding:12px;border-radius:10px;border:1px solid #53627a;background:#111b2b;color:inherit;font:inherit}
textarea{min-height:125px;resize:vertical}
.row{display:flex;gap:10px;flex-wrap:wrap}.row>*{flex:1;min-width:140px}
button{padding:12px 16px;border:0;border-radius:10px;background:#a9d3ff;color:#102038;font-weight:700;font-size:1rem;cursor:pointer}
button:disabled{opacity:.5;cursor:wait}
small,.status{color:#c1cce0}.status{min-height:1.5em;margin-top:10px}
audio{width:100%;margin-top:12px}
.preset{background:#34445e;color:#fff;margin:4px 4px 4px 0}
</style>
</head>
<body><main>
<h1>🗣️ PadippuPal Voice Lab</h1>
<p class="sub">Preview Kokoro voices for a gentle, patient study companion.</p>
<div class="panel">
<label for="token">Test API token</label>
<input id="token" type="password" autocomplete="off" placeholder="Paste the TTS_API_TOKEN set in Space secrets">
<small>Used only in this page's memory to call this same service. It is not saved.</small>
<label for="voice">Voice</label>
<select id="voice">
<option value="af_heart">af_heart — warm female-style voice</option>
<option value="af_bella">af_bella — female-style voice</option>
<option value="af_nicole">af_nicole — female-style voice</option>
<option value="af_sarah">af_sarah — female-style voice</option>
<option value="am_adam">am_adam — male-style voice</option>
<option value="am_michael">am_michael — male-style voice</option>
</select>
<div class="row">
<div><label for="speed">Speaking speed: <span id="speedLabel">0.90×</span></label><input id="speed" type="range" min="0.7" max="1.3" step="0.05" value="0.9"></div>
<div><label for="text">Sample text</label><button class="preset" id="english" type="button">English sample</button><button class="preset" id="tanglish" type="button">Tanglish sample</button></div>
</div>
<label for="text">What should the teacher say?</label>
<textarea id="text">Hello, my dear! Don't worry if this feels difficult. We'll learn slowly, step by step, together. You're doing a lovely job!</textarea>
<button id="play" type="button">Generate and play voice</button>
<div class="status" id="status" role="status" aria-live="polite">Ready when you are.</div>
<audio id="audio" controls hidden></audio>
</div>
<p class="sub">Note: Kokoro's built-in voices are not specifically trained as a motherly teacher voice. English is the first quality test; Tanglish/Tamil pronunciation may vary.</p>
</main>
<script>
const $=id=>document.getElementById(id);
let currentUrl=null;
$('speed').addEventListener('input',()=> $('speedLabel').textContent=Number($('speed').value).toFixed(2)+'×');
$('english').onclick=()=>{$('text').value="Hello, my dear! Don't worry if this feels difficult. We'll learn slowly, step by step, together. You're doing a lovely job!";};
$('tanglish').onclick=()=>{$('text').value="Kanna, கவலைப்படாதே. Namma innaikku konjam konjama padikkalaam. Unakku puriyura varaikkum naan help panren. Super-aa try panra!";};
$('play').onclick=async()=>{
 const token=$('token').value.trim(), text=$('text').value.trim();
 if(!token){$('status').textContent='Enter the server TTS_API_TOKEN first.';return;}
 if(!text){$('status').textContent='Type a sample sentence first.';return;}
 const button=$('play');button.disabled=true;$('status').textContent='Generating audio… first run can take a little while.';
 try{
  const response=await fetch('/tts',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},body:JSON.stringify({text,voice:$('voice').value,speed:Number($('speed').value)})});
  if(!response.ok){let message='HTTP '+response.status;try{const body=await response.json();message=body.detail||message;}catch{}throw new Error(message);}
  const blob=await response.blob();
  if(currentUrl)URL.revokeObjectURL(currentUrl);
  currentUrl=URL.createObjectURL(blob);$('audio').src=currentUrl;$('audio').hidden=false;
  await $('audio').play();$('status').textContent='Audio generated. Compare voices and speed, then listen again with the player.';
 }catch(error){$('status').textContent='Could not generate audio: '+error.message;}
 finally{button.disabled=false;}
};
</script></body></html>
""")


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
