# Jarvis Architecture

Jarvis Phase 1 is intentionally small. It establishes the runtime shape for a
Raspberry Pi voice assistant without implementing assistant features beyond
local wake-word detection.

## Current Phase 1 Flow

```text
Microphone
    |
    v
AudioInput
    |
    v
WakeWordDetector
    |
    v
OpenWakeWordDetector
    |
    v
Detection Event
    |
    v
Logger
```

## Current Components

### Configuration

`jarvis.config.Settings` loads the Phase 1 environment variables once at
startup and validates them before hardware or model initialization begins.

### Audio

`jarvis.audio.interface.AudioInput` defines the microphone boundary.
`SoundDeviceMicrophone` is the current implementation and is responsible for
opening the input device, reading 16 kHz mono int16 audio chunks, and releasing
the stream during shutdown.

The wake-word detector does not own or configure the physical microphone.

### Wake Word

`jarvis.wakeword.interface.WakeWordDetector` defines the provider-independent
wake-word boundary.

`OpenWakeWordDetector` is the current provider adapter. It loads the
openWakeWord model once during startup and returns detection events when model
scores meet the configured threshold.

### Debounce

`WakeWordDebouncer` suppresses repeated positive frames from a single spoken
wake word. This logic is provider-independent and unit tested without a
microphone or openWakeWord.

### Application Lifecycle

`jarvis.main.JarvisApp` composes configuration, audio input, wake-word
detection, and debouncing. It handles `SIGINT` and `SIGTERM`, stops hardware
resources cleanly, and exits with a non-zero status on unrecoverable startup or
runtime errors.

## Docker Runtime

The container runs the Python application directly and maps `/dev/snd` from the
Raspberry Pi host so ALSA devices are visible inside the container. It does not
expose network ports and does not run an API server.

## Future Architecture

The planned assistant flow is future work and is not implemented in Phase 1.

```text
Wake Word
    |
    v
Audio Capture
    |
    v
Speech-to-Text
    |
    v
Conversation Manager
    |
    v
LLM
    |
    v
Tools
    |
    v
Text-to-Speech
    |
    v
Speaker
```

Future package ownership is expected to grow along these lines:

```text
jarvis/
├── audio/
├── wakeword/
├── stt/          # future
├── llm/          # future
├── tts/          # future
├── tools/        # future
├── memory/       # future
└── conversation/ # future
```

Those future directories are not created yet because Phase 1 should not contain
placeholder functionality.
