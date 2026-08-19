from __future__ import annotations

import sounddevice as sd


def main() -> int:
    print(sd.query_devices())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
