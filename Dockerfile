FROM debian:trixie-slim

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV APP_CONFIG=/opt/uniquode.io/uniquode.io.toml \
    HOME=/home/uniquode \
    PATH="/opt/uniquode.io/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/uniquode.io/.venv \
    UV_PYTHON=3.14 \
    UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    XDG_DATA_HOME=/home/uniquode/.local/share

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    dbus-user-session \
    git \
    gnome-keyring \
    libsecret-tools \
    && groupadd --system --gid 10001 uniquode \
    && useradd \
        --system \
        --uid 10001 \
        --gid 10001 \
        --create-home \
        --home-dir /home/uniquode \
        --shell /bin/bash \
        uniquode \
    && mkdir -p \
        /home/uniquode/.local/share/keyrings \
        /opt/uniquode.io \
    && chown -R uniquode:uniquode \
        /home/uniquode \
        /opt/uniquode.io \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --chmod=0755 startup.sh /usr/local/bin/uniquode-start

RUN uv python install 3.14 \
    && chmod -R a+rX /opt/uv/python \
    && chown -R uniquode:uniquode /home/uniquode

COPY --chown=uniquode:uniquode . /opt/uniquode.io

USER uniquode
WORKDIR /opt/uniquode.io

RUN python_bin="$(uv python find 3.14)" \
    && "$python_bin" ci/ensure_wybra_git_source.py normalise-git \
    && uv lock --upgrade-package wybra \
    && mkdir -p media static \
    && uv sync --frozen --no-dev

EXPOSE 8000

ENTRYPOINT ["dbus-run-session", "--", "/usr/local/bin/uniquode-start"]
