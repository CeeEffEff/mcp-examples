# Use official uv Python image with specified Python version
ARG PYTHON_VERSION
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install dependencies using uv (no requirements.txt needed)
RUN --mount=type=cache,target=/root/.cache/uv \
--mount=type=bind,source=uv.lock,target=uv.lock \
--mount=type=bind,source=pyproject.toml,target=pyproject.toml \
uv sync --locked --no-install-project --no-dev

# Copy source code and install
COPY main /app
RUN --mount=type=cache,target=/root/.cache/uv \
uv sync --locked --no-dev

# Set executable path
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

ENTRYPOINT []
# Run the service by default
CMD ["uv", "run", "python", "main.py"]