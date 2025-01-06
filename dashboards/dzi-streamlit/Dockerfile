FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

RUN mkdir /dashboard
WORKDIR /dashboard

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=/dashboard/uv.lock,target=uv.lock \
    --mount=type=bind,source=/dashboard/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

RUN useradd -ms /bin/bash streamlit

ADD ./dashboard/*.py /dashboard

USER streamlit

CMD ["./.venv/bin/streamlit", "run", "./dashboard.py"]
