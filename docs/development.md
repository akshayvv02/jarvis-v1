# Development

## Local Setup

Install `uv`, then create the environment:

```bash
uv sync
```

Run unit tests:

```bash
uv run pytest
```

Run the package entry point:

```bash
uv run python -m jarvis
```

On macOS this command requires a working microphone and local audio permissions.
Most unit tests do not require microphone hardware or Sarvam network access.
Gemini and Sarvam integration tests are opt-in and skipped by default.

Run Gemini integration tests only when you intentionally want to call the API:

```bash
GEMINI_INTEGRATION_TESTS=true uv run pytest tests/integration/test_gemini_integration.py
```

## Personality Evaluation

Phase 3.1 personality behavior is evaluated manually because LLM output is
nondeterministic. Use `docs/personality-evaluation.md` as the prompt set and
score responses for naturalness, brevity, language matching, serious-context
handling, and voice readability.

## Audio Device Discovery

List devices through the Python audio stack:

```bash
uv run python scripts/list_audio_devices.py
```

On Raspberry Pi, also list ALSA recording devices:

```bash
arecord -l
```

If the default input is not correct, set `JARVIS_AUDIO_DEVICE` in `.env`.

## Docker Development

Build the image:

```bash
docker compose build
```

Start Jarvis:

```bash
docker compose up
```

View logs:

```bash
docker compose logs -f jarvis
```

Stop Jarvis:

```bash
docker compose down
```
