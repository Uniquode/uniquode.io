#!/usr/bin/env bash
set -euo pipefail

: "${WYBRA_KEYRING_PASSWORD:?WYBRA_KEYRING_PASSWORD must be set}"

keyring_env=/tmp/wybra-keyring-env
umask 077
printf '%s\n' "$WYBRA_KEYRING_PASSWORD" \
  | gnome-keyring-daemon --unlock --components=secrets >"$keyring_env"

# shellcheck disable=SC1090
. "$keyring_env"

exec uv run --frozen --no-dev wybra-runserver \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8000}" \
  --no-reload
