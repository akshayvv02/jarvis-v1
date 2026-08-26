from __future__ import annotations

import argparse
import math
import time

import numpy as np

from jarvis.audio.microphone import SoundDeviceMicrophone
from jarvis.config import Settings


def main() -> int:
    args = _parse_args()
    settings = Settings.from_env()
    device = _audio_device_arg(args.device) if args.device is not None else settings.audio_device

    microphone = SoundDeviceMicrophone(
        device=device,
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        chunk_size=settings.chunk_size,
    )

    print("Starting live mic meter. Press Ctrl+C to stop.")
    print(f"device={device or 'default'} sample_rate={settings.sample_rate} channels={settings.channels}")

    try:
        microphone.start()
        started = time.monotonic()
        while args.duration_seconds is None or time.monotonic() - started < args.duration_seconds:
            chunk = microphone.read()
            rms, peak, dbfs = _levels(chunk.samples)
            print(_format_meter(rms=rms, peak=peak, dbfs=dbfs), end="\r", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        print()
        microphone.stop()

    return 0


def _levels(samples: np.ndarray) -> tuple[float, int, float]:
    values = samples.astype(np.float32)
    rms = float(np.sqrt(np.mean(values**2))) if values.size else 0.0
    peak = int(np.max(np.abs(values))) if values.size else 0
    dbfs = -math.inf if rms <= 0 else 20 * math.log10(rms / 32768)
    return rms, peak, dbfs


def _format_meter(*, rms: float, peak: int, dbfs: float) -> str:
    level = min(1.0, rms / 12000)
    filled = round(level * 40)
    bar = "#" * filled + "-" * (40 - filled)
    dbfs_text = "-inf" if math.isinf(dbfs) else f"{dbfs:5.1f}"
    return f"rms={rms:7.1f} peak={peak:5d} dbfs={dbfs_text} [{bar}]"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show a live microphone input meter.")
    parser.add_argument(
        "--device",
        help="Optional sounddevice input id/name. Defaults to JARVIS_AUDIO_DEVICE.",
    )
    parser.add_argument(
        "--duration-seconds",
        type=float,
        help="Optional number of seconds to run. Defaults to running until Ctrl+C.",
    )
    return parser.parse_args()


def _audio_device_arg(value: str) -> int | str:
    if value.isdigit():
        return int(value)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
