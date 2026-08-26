# Jarvis

Jarvis is a self-hosted Raspberry Pi voice assistant foundation. Phase 3 listens
for "Hey Jarvis", plays a local acknowledgement sound, records the spoken query,
sends that short WAV file to Sarvam Saaras STT, streams a Gemini response, and
returns to wake-word listening.

Current capability:

```text
Microphone -> openWakeWord -> acknowledgement -> query recording -> Sarvam STT -> Jarvis personality -> Gemini -> terminal response
```

No TTS, tools, memory, web search, smart-home integration, or API server is
implemented in Phase 3.

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

Phase 3 variables:

```text
JARVIS_LOG_LEVEL=INFO
SARVAM_API_KEY=
SARVAM_STT_MODEL=saaras:v3
SARVAM_STT_MODE=transcribe
SARVAM_STT_LANGUAGE_CODE=unknown
SARVAM_STT_TIMEOUT_SECONDS=30
JARVIS_LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_REQUEST_TIMEOUT_SECONDS=30
JARVIS_PERSONALITY=indian_casual
JARVIS_HUMOR_LEVEL=2
JARVIS_PROMPT_DEBUG=false
JARVIS_AUDIO_DEVICE=
JARVIS_AUDIO_OUTPUT_DEVICE=
JARVIS_SAMPLE_RATE=16000
JARVIS_CHANNELS=1
JARVIS_CHUNK_SIZE=1280
JARVIS_AUDIO_FLUSH_DURATION_MS=300
JARVIS_ACK_AUDIO_PATH=assets/audio/acknowledgement.wav
JARVIS_WAKEWORD_MODEL=hey_jarvis
JARVIS_WAKEWORD_THRESHOLD=0.5
JARVIS_WAKEWORD_COOLDOWN_MS=1500
JARVIS_WAKEWORD_RESUME_DELAY_MS=1500
JARVIS_WAKEWORD_RESET_DURATION_MS=1500
JARVIS_QUERY_MAX_DURATION_SECONDS=30
JARVIS_QUERY_NO_SPEECH_TIMEOUT_SECONDS=5
JARVIS_SILENCE_DURATION_MS=1000
JARVIS_SPEECH_START_THRESHOLD=500
JARVIS_QUERY_TEMP_DIR=/tmp/jarvis
JARVIS_CLEANUP_QUERY_AUDIO=true
```

Leave `JARVIS_AUDIO_DEVICE` empty to use the default input device. On
Raspberry Pi, a numeric PortAudio/sounddevice device id is often more reliable
than an ALSA name.

Set your real Sarvam and Gemini keys only in `.env`:

```text
SARVAM_API_KEY=your_real_key_here
GEMINI_API_KEY=your_real_key_here
```

Personality currently affects only the LLM response style. It does not add
memory, tools, TTS, weather, alarms, reminders, or smart-home actions.

Humor levels:

```text
0 = professional
1 = friendly
2 = witty, default
3 = more playful
```

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
2026-08-19 13:00:01 INFO jarvis.main: Personality: indian_casual version=jarvis-indian-v1 humor_level=2
2026-08-19 13:00:01 INFO jarvis.main: Listening for "Hey Jarvis"...
2026-08-19 13:00:08 INFO jarvis.main: WAKE WORD DETECTED: hey_jarvis score=0.812
2026-08-19 13:00:08 INFO jarvis.audio.playback: Acknowledgement played
2026-08-19 13:00:09 INFO jarvis.audio.recorder: Listening for query speech
2026-08-19 13:00:12 INFO jarvis.stt.sarvam: Transcription completed
2026-08-19 13:00:12 INFO jarvis.main: You said: "bhai kal Bangalore mein baarish hogi kya"
2026-08-19 13:00:12 INFO jarvis.main: Assistant state: processing
Jarvis: Haan, main short answer mein bata sakta hoon...
2026-08-19 13:00:13 INFO jarvis.llm.gemini: LLM response completed
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
- Run `docker compose run --rm --entrypoint /app/.venv/bin/python jarvis -c "import sounddevice as sd; print(sd.query_devices())"`.
- Set `JARVIS_AUDIO_DEVICE` to the numeric input device shown by sounddevice.
  For example: `JARVIS_AUDIO_DEVICE=1`.

Invalid sample rate:

- Jarvis first tries `JARVIS_SAMPLE_RATE`, default `16000`.
- If the mic rejects that rate, Jarvis retries with the device default rate and
  resamples internally to 16 kHz for openWakeWord.

openWakeWord model unavailable:

- Rebuild the image with internet access: `docker compose build --no-cache`.
- Confirm the build step that downloads openWakeWord models completed.

Sarvam key missing:

- Put `SARVAM_API_KEY=...` in `.env`.
- Do not commit `.env`.

Gemini key missing:

- Put `GEMINI_API_KEY=...` in `.env`.
- Do not commit `.env`.

No query detected after acknowledgement:

- Lower `JARVIS_SPEECH_START_THRESHOLD`.
- Increase `JARVIS_QUERY_NO_SPEECH_TIMEOUT_SECONDS` if you pause before speaking.

No detections:

- Confirm sample rate is `16000`, channels is `1`, and chunk size is `1280`.
- Lower `JARVIS_WAKEWORD_THRESHOLD` slightly for testing.
- Speak clearly near the microphone.

Excessive false positives:

- Increase `JARVIS_WAKEWORD_THRESHOLD`.
- Increase `JARVIS_WAKEWORD_COOLDOWN_MS` if one utterance logs repeatedly.

Immediate re-trigger after transcription:

- Increase `JARVIS_WAKEWORD_RESUME_DELAY_MS`.
- Increase `JARVIS_WAKEWORD_RESET_DURATION_MS`.
- Jarvis should return to `Listening for "Hey Jarvis"...` and wait for a fresh
  wake-word utterance before recording another query.

## Phase 2 Validation Checklist

- Host microphone is visible with `arecord -l`.
- Microphone is visible inside Docker.
- Container starts successfully.
- openWakeWord initializes successfully.
- Jarvis logs `Listening for "Hey Jarvis"...`.
- Saying "Hey Jarvis" logs a detection and plays the local acknowledgement.
- Jarvis records only the query after the acknowledgement.
- Jarvis sends the temporary WAV to Sarvam and prints the transcript.
- Temporary query audio is cleaned up after successful transcription.
- Repeated frames from one utterance are debounced.
- Jarvis returns to wake-word detection after transcription.
- `docker compose down` shuts down cleanly.
- Container restarts with Docker Compose restart policy.
- CPU and memory usage are observed on the Pi with `docker stats`.

## Documentation

- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Audio](docs/audio.md)
