---
title: PadippuPal Kokoro TTS
emoji: 🗣️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# PadippuPal Kokoro TTS — isolated prototype

This is a standalone, CPU-based Kokoro speech API prototype. It does **not** change the PadippuPal Android app or its production Render backend.

## Deploy to a Hugging Face Space

1. Create a new **private Docker Space** if private Spaces are available to your account, or a public Space with no private content in its repository.
2. Upload the contents of this folder to the Space repository (the Dockerfile must be at the Space repository root).
3. In Space **Settings → Variables and secrets**, add a secret named `TTS_API_TOKEN` with a long random value.
4. Wait for the first build; the first request may be slow while model weights download and load.

Free CPU Spaces can sleep when idle and may have cold-start latency. This is a test endpoint, not a guaranteed always-on production service.

## API

- `GET /` — service information
- `GET /health` — lightweight health check
- `POST /tts` — returns 24 kHz mono WAV audio

Example request:

```bash
curl -X POST "https://YOUR-SPACE.hf.space/tts" \
  -H "Authorization: Bearer YOUR_TTS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello! Let us learn this together.","voice":"af_heart","speed":1.0}' \
  --output sample.wav
```

Supported initial voices: `af_heart`, `af_bella`, `af_nicole`, `af_sarah`, `am_adam`, `am_michael`. English is the initial test target. Tamil/Tanglish quality is not guaranteed and must be evaluated separately.

Never put the API token in the Android APK or expose it in client-side code. The PadippuPal backend should call this service using a server-side secret. Keep the existing Gemini/Android fallback until real end-to-end tests pass.
