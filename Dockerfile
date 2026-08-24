FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        alsa-utils \
        libasound2 \
        libportaudio2 \
        portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY assets ./assets

RUN uv sync --frozen --no-dev

RUN uv run --frozen python -c "import openwakeword; openwakeword.utils.download_models(model_names=['hey_jarvis'])"

RUN useradd --create-home --shell /usr/sbin/nologin jarvis \
    && chown -R jarvis:jarvis /app

USER jarvis

CMD ["uv", "run", "--frozen", "python", "-m", "jarvis"]
