# Audio Notes

Jarvis standardizes wake-word and query audio to 16 kHz mono 16-bit PCM.

Some USB microphones, including common wireless creator microphones, expose a
native 48 kHz input and reject direct 16 kHz capture. Jarvis first tries the
configured target rate. If the device rejects it, the microphone adapter opens
the device at its default input rate and resamples each chunk to 16 kHz before
wake-word detection or query recording.

On Raspberry Pi, inspect devices with:

```bash
arecord -l
docker compose run --rm --entrypoint /app/.venv/bin/python jarvis -c "import sounddevice as sd; print(sd.query_devices())"
```

Use the numeric `sounddevice` input id in `.env` when the default device is not
the microphone:

```text
JARVIS_AUDIO_DEVICE=1
```

The acknowledgement sound is local and should be short. Query recording starts
after playback and after a short microphone flush so the wake word and
acknowledgement are not uploaded to Sarvam.

Phase 4 also plays synthesized Sarvam TTS WAV files through the same
`AudioOutput` layer.

## Wired Speaker

For the Raspberry Pi runtime, prefer a wired AUX speaker connected to the Pi's
3.5 mm output. This avoids Bluetooth latency, dynamic device IDs, sleep behavior,
and container passthrough complexity.

Verify host playback first:

```bash
cd ~/Desktop/apps/jarvis-v1
aplay assets/audio/acknowledgement.wav
```

Then inspect Docker audio devices:

```bash
docker compose run --rm --entrypoint /app/.venv/bin/python jarvis -c "import sounddevice as sd; print(sd.query_devices())"
```

If the 3.5 mm output appears as `bcm2835 Headphones` at device `0`, configure:

```text
JARVIS_AUDIO_OUTPUT_DEVICE=0
```
