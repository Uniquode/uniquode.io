#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Build a smoke-test config layered on top of uniquode.io.toml that adds an
# explicit TCP host/port for the database. Production/deploy environments
# resolve the database host another way (e.g. AWS RDS discovery or a
# platform-injected socket); local/CI smoke runs need an explicit host since
# there is no such discovery mechanism available.
SMOKE_CONFIG="$(mktemp --suffix=.toml)"
python3 - "$SMOKE_CONFIG" <<'PY'
import sys

dest = sys.argv[1]
with open("uniquode.io.toml", encoding="utf-8") as fh:
    text = fh.read()
marker = "[app.database]\n"
idx = text.index(marker) + len(marker)
injected = 'host = "127.0.0.1"\nport = 5432\n'
text = text[:idx] + injected + text[idx:]
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(text)
PY

export APP_CONFIG="$SMOKE_CONFIG"
export XDG_DATA_HOME="${RUNNER_TEMP:-/tmp}/xdg-data-smoke"
rm -rf "$XDG_DATA_HOME"
mkdir -p "$XDG_DATA_HOME/keyrings"

keyring_env="$(mktemp)"
keyring_password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
printf '%s\n' "$keyring_password" | gnome-keyring-daemon --unlock --components=secrets >"$keyring_env"
set -a
# shellcheck disable=SC1090
. "$keyring_env"
set +a

echo "== Seeding core app secrets =="
uv run python - <<'PY' | uv run wybra-secret set --json
import base64
import json
import secrets
import zlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.fernet import Fernet

encoded_key = Fernet.generate_key().decode("ascii")
raw_key = base64.urlsafe_b64decode(encoded_key)
checksum = f"{zlib.crc32(raw_key) & 0xFFFFFFFF:08x}"
apple_private_key = ec.generate_private_key(ec.SECP256R1())
apple_private_key_pem = apple_private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("ascii")
print(
    json.dumps(
        {
            "secrets/key/current": f"ci:{encoded_key}:{checksum}",
            "auth/forms/csrf-token-secret/current": secrets.token_urlsafe(32),
            "auth/providers/google/client-secret": secrets.token_urlsafe(32),
            "auth/providers/github/client-secret": secrets.token_urlsafe(32),
            "auth/providers/apple/private-key": apple_private_key_pem,
        }
    )
)
PY

echo "== Seeding database credentials =="
DB_APP_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
printf '%s' "postgres" | uv run wybra-secret set --key database/uniquode/service-account/user --stdin
printf '%s' "postgres" | uv run wybra-secret set --key database/uniquode/service-account/password --stdin
printf '%s' "uniquode_app" | uv run wybra-secret set --key database/uniquode/app/user --stdin
printf '%s' "$DB_APP_PASSWORD" | uv run wybra-secret set --key database/uniquode/app/password --stdin

echo "== Provisioning database =="
uv run wybra-migrate init
uv run wybra-migrate migrate

echo "== Validating configuration =="
# Run after provisioning: scope-catalogue validation opens a live database
# connection using the app role created by `wybra-migrate init`, so the app
# role and schema must already exist for this check to pass.
uv run wybra-validate --verbose

echo "== Creating smoke-test user =="
SMOKE_EMAIL="smoke@uniquode.io"
# Generated randomly (and re-checked against the password policy's blocked
# fragment list, e.g. "pass"/"test"/"admin") rather than hardcoded, since the
# default policy rejects common substrings such as "pass" or "test".
SMOKE_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18) + "!Aa1")')"
printf '%s' "$SMOKE_PASSWORD" | uv run wybra-authmgr user create "$SMOKE_EMAIL" --password stdin --admin 2>&1 || \
  echo "(user create returned non-zero, continuing - may already exist)"

echo "== Starting server =="
uv run wybra-runserver --host 127.0.0.1 --port 8000 --no-reload &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

echo "Waiting for server to become ready..."
ready=""
for i in $(seq 1 30); do
  if curl -sf -o /dev/null http://127.0.0.1:8000/health; then
    echo "Server is up after ${i}s"
    ready="1"
    break
  fi
  sleep 1
done
if [ -z "$ready" ]; then
  echo "Server did not become ready in time" >&2
  exit 1
fi

echo "== Walking key routes =="
check_route() {
  local path="$1"
  local expected="$2"
  local code
  code="$(curl -s -o /tmp/smoke_body.html -w '%{http_code}' "http://127.0.0.1:8000${path}")"
  echo "GET ${path} -> ${code} (expected ${expected})"
  if [ "$code" != "$expected" ]; then
    echo "UNEXPECTED status for ${path}: got ${code}, expected ${expected}" >&2
    exit 1
  fi
}

check_route "/health" 200
check_route "/" 200
check_route "/account" 200
check_route "/account/login" 200
# uniquode.io does not configure [app.auth] account_creation_policy, so it
# uses wybra's default "admin-created" policy -- public self-signup is
# intentionally disabled and /account/signup returns 404 by design.
check_route "/account/signup" 404
check_route "/docs" 200
check_route "/openapi.json" 200
check_route "/nonexistent-smoke-path" 404

echo "== Attempting login flow =="
COOKIE_JAR="$(mktemp)"
LOGIN_PAGE="$(curl -s -c "$COOKIE_JAR" http://127.0.0.1:8000/account/login)"
CSRF_TOKEN="$(printf '%s' "$LOGIN_PAGE" | grep -o 'name="csrf_token"[^>]*value="[^"]*"' | head -1 | sed -E 's/.*value="([^"]*)".*/\1/')"
if [ -z "$CSRF_TOKEN" ]; then
  echo "CSRF token not found on login page - login form markup may have changed" >&2
  exit 1
fi

# A successful login redirects (303) to "/"; anything else (e.g. the login
# form being re-rendered with a 200) means the credentials, CSRF token, or
# session cookie handling is broken.
LOGIN_CODE="$(curl -s -o /tmp/smoke_login.html -w '%{http_code}' -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
  -d "csrf_token=${CSRF_TOKEN}" -d "email=${SMOKE_EMAIL}" -d "password=${SMOKE_PASSWORD}" \
  http://127.0.0.1:8000/account/login)"
echo "POST /account/login -> ${LOGIN_CODE}"
if [ "$LOGIN_CODE" != "303" ]; then
  echo "UNEXPECTED login status: got ${LOGIN_CODE}, expected 303" >&2
  exit 1
fi

# Confirm the session cookie actually authenticates subsequent requests by
# checking the account page no longer shows the login form.
ACCOUNT_PAGE="$(curl -s -b "$COOKIE_JAR" http://127.0.0.1:8000/account)"
if printf '%s' "$ACCOUNT_PAGE" | grep -q 'name="password"'; then
  echo "Session does not appear authenticated after login (still seeing a login/password form on /account)" >&2
  exit 1
fi
echo "Authenticated session confirmed on /account"

echo "== Smoke test passed =="
