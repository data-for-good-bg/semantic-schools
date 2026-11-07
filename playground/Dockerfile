# syntax=docker/dockerfile:1.4

# Choose a python version that you know works with your application
FROM python:3.10-slim

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv
ENV UV_SYSTEM_PYTHON=1

WORKDIR /work

# Copy requirements file
COPY --link requirements.txt .

# Install the requirements using uv
RUN uv pip install -r requirements.txt

EXPOSE 8080

# Create a non-root user and switch to it
RUN useradd -m app_user
USER app_user

CMD [ "marimo", "edit", "/work", "--host", "0.0.0.0", "-p", "8080" ]