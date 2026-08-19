# Jarvis

Jarvis is a self-hosted Raspberry Pi voice assistant foundation. Phase 1 only
does local wake-word detection for "Hey Jarvis" and logs detections in the
terminal.

Current capability:

```text
Microphone -> openWakeWord -> "Hey Jarvis" -> terminal detection
```

No STT, LLM, TTS, tools, memory, web search, smart-home integration, or API
server is implemented in Phase 1.

## Requirements

- Raspberry Pi 4 or newer
- 64-bit Raspberry Pi OS
- Docker and Docker Compose
- Working microphone visible to ALSA
- Internet during image build to install dependencies and cache openWakeWord
  models

Wake-word detection itself runs locally and does not send microphone audio to an
external service.

## Development

Install `uv`, then run:

```bash
uv sync
uv run pytest
```

To list local audio devices:

```bash
uv run python scripts/list_audio_devices.py
```

To run directly on a development machine:

```bash
uv run python -m jarvis
```

macOS development is useful for unit tests and package work. Raspberry Pi audio
and Docker validation must be done on the Pi.

## Configuration

Copy the example environment file when you need local overrides:

```bash
cp .env.example .env
```

Phase 1 variables:

```text
JARVIS_LOG_LEVEL=INFO
JARVIS_AUDIO_DEVICE=
JARVIS_SAMPLE_RATE=16000
JARVIS_CHANNELS=1
JARVIS_CHUNK_SIZE=1280
JARVIS_WAKEWORD_MODEL=hey_jarvis
JARVIS_WAKEWORD_THRESHOLD=0.5
JARVIS_WAKEWORD_COOLDOWN_MS=1500
```

Leave `JARVIS_AUDIO_DEVICE` empty to use the default input device.

## Raspberry Pi Audio Setup

Check that the microphone is visible on the host:

```bash
arecord -l
```

Check that ALSA devices exist:

```bash
ls -la /dev/snd
```

If the host cannot see the microphone, fix that before starting Docker.

## Docker

Build and start:

```bash
docker compose build
docker compose up
```

The Compose file maps `/dev/snd` into the container and adds the container user
to the `audio` group. If your Pi uses a non-default capture device, set
`JARVIS_AUDIO_DEVICE` in `.env`.

Inspect logs:

```bash
docker compose logs -f jarvis
```

Stop:

```bash
docker compose down
```

## Validate Audio Inside Docker

Start a shell in the built image:

```bash
docker compose run --rm jarvis arecord -l
```

The microphone should appear inside the container. If it does not, check
`/dev/snd`, host permissions, and Compose device mapping.

## Expected Logs

```text
2026-08-19 13:00:00 INFO jarvis.main: Jarvis starting
2026-08-19 13:00:01 INFO jarvis.audio.microphone: Audio input initialized
2026-08-19 13:00:01 INFO jarvis.wakeword.openwakeword_detector: Wake-word detector initialized
2026-08-19 13:00:01 INFO jarvis.main: Listening for "Hey Jarvis"...
2026-08-19 13:00:08 INFO jarvis.main: WAKE WORD DETECTED: hey_jarvis score=0.812
```

## Troubleshooting

Microphone not detected:

- Run `arecord -l` on the Pi host.
- Try another USB port or confirm the USB microphone is powered.

`/dev/snd` unavailable:

- Confirm the Pi has audio devices with `ls -la /dev/snd`.
- Confirm Compose includes `/dev/snd:/dev/snd`.

Permission problems:

- Confirm the container has `group_add: [audio]`.
- Check host permissions on `/dev/snd/*`.

Incorrect ALSA device:

- Run `arecord -l`.
- Set `JARVIS_AUDIO_DEVICE` to the correct device.

openWakeWord model unavailable:

- Rebuild the image with internet access: `docker compose build --no-cache`.
- Confirm the build step that downloads openWakeWord models completed.

No detections:

- Confirm sample rate is `16000`, channels is `1`, and chunk size is `1280`.
- Lower `JARVIS_WAKEWORD_THRESHOLD` slightly for testing.
- Speak clearly near the microphone.

Excessive false positives:

- Increase `JARVIS_WAKEWORD_THRESHOLD`.
- Increase `JARVIS_WAKEWORD_COOLDOWN_MS` if one utterance logs repeatedly.

## Phase 1 Validation Checklist

- Host microphone is visible with `arecord -l`.
- Microphone is visible inside Docker.
- Container starts successfully.
- openWakeWord initializes successfully.
- Jarvis logs `Listening for "Hey Jarvis"...`.
- Saying "Hey Jarvis" logs a detection.
- Repeated frames from one utterance are debounced.
- Jarvis continues listening after detection.
- `docker compose down` shuts down cleanly.
- Container restarts with Docker Compose restart policy.
- CPU and memory usage are observed on the Pi with `docker stats`.

## Documentation

- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
