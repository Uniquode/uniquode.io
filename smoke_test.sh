#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Both BSD and GNU mktemp randomise a directory template ending in Xs.
SMOKE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/uniquode-smoke.XXXXXX")"

cleanup() {
  local status=$?
  if [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  if [ -f "$SMOKE_DIR/keychain.json" ]; then
    uv run --locked python -m ci.smoke_fixtures cleanup "$SMOKE_DIR" || status=1
  fi
  rm -r -- "$SMOKE_DIR"
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "== Checking Redis and preparing the smoke keychain =="
uv run --locked python -m ci.smoke_fixtures prepare "$SMOKE_DIR"
export APP_CONFIG="$SMOKE_DIR/config.toml"
unset SMOKE_REDIS_URL POSTGRES_SUPERUSER_PASSWORD

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
  code="$(curl -s -o "$SMOKE_DIR/response.html" -w '%{http_code}' "http://127.0.0.1:8000${path}")"
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
COOKIE_JAR="$SMOKE_DIR/cookies"
LOGIN_PAGE="$(curl -s -c "$COOKIE_JAR" http://127.0.0.1:8000/account/login)"
# The trailing `|| true` keeps a no-match `grep` from tripping `set -e` and
# aborting the script before the clearer diagnostic below can run.
CSRF_TOKEN="$(printf '%s' "$LOGIN_PAGE" | grep -o 'name="csrf_token"[^>]*value="[^"]*"' | head -1 | sed -E 's/.*value="([^"]*)".*/\1/')" || true
if [ -z "$CSRF_TOKEN" ]; then
  echo "CSRF token not found on login page - login form markup may have changed" >&2
  exit 1
fi

# A successful login redirects (303) to "/"; anything else (e.g. the login
# form being re-rendered with a 200) means the credentials, CSRF token, or
# session cookie handling is broken.
LOGIN_CODE="$(curl -s -o "$SMOKE_DIR/login.html" -w '%{http_code}' -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
  --data-urlencode "csrf_token=${CSRF_TOKEN}" --data-urlencode "email=${SMOKE_EMAIL}" --data-urlencode "password=${SMOKE_PASSWORD}" \
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
