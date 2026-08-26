from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if level != "DEBUG":
        logging.getLogger("google_genai").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
