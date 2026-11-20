"""Prepare and remove the keychain entries owned by one smoke run."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import tomllib
from pathlib import Path
from uuid import uuid4

import keyring
from ci.seed_core_secrets import build_secrets, store_secrets
from keyring.errors import KeyringError
from redis import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

KEYCHAIN_MANIFEST = "keychain.json"
SMOKE_SERVICE = re.compile(r"uniquode-smoke-[0-9a-f]{32}")


class SmokeFixtureError(Exception):
    """Report invalid or unavailable smoke fixtures."""


def check_redis(url: str) -> None:
    try:
        with Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry=Retry(NoBackoff(), 0),
        ) as client:
            if client.ping() is not True:
                raise SmokeFixtureError("Smoke Redis did not respond to PING.")
            settings = client.config_get("appendonly", "maxmemory-policy")
    except RedisError, ValueError:
        raise SmokeFixtureError("Cannot reach or inspect Redis at SMOKE_REDIS_URL.") from None

    eviction_policy = settings.get("maxmemory-policy")
    if settings.get("appendonly") != "yes" or not eviction_policy or eviction_policy.startswith("allkeys-"):
        raise SmokeFixtureError("Smoke Redis requires appendonly yes and a non-allkeys eviction policy.")


def write_config(path: Path, service: str, postgres_port: int) -> None:
    text = Path("uniquode.io.toml").read_text(encoding="utf-8")
    database_header = "[app.database]\n"
    keychain_setting = '[secrets.keychain]\nappname = "wybra"\n'
    if text.count(database_header) != 1 or text.count(keychain_setting) != 1:
        raise SmokeFixtureError("Cannot locate the database and Wybra keychain settings in uniquode.io.toml.")

    text = text.replace(database_header, f'{database_header}host = "127.0.0.1"\nport = {postgres_port}\n')
    text = text.replace(keychain_setting, f'[secrets.keychain]\nappname = "{service}"\n')
    tomllib.loads(text)
    path.write_text(text, encoding="utf-8")


def prepare(directory: Path) -> None:
    redis_url = os.environ.get("SMOKE_REDIS_URL")
    if not redis_url:
        raise SmokeFixtureError("Set SMOKE_REDIS_URL to the URL of a disposable Redis instance.")
    postgres_password = os.environ.get("POSTGRES_SUPERUSER_PASSWORD")
    if not postgres_password:
        raise SmokeFixtureError("Set POSTGRES_SUPERUSER_PASSWORD for the disposable PostgreSQL instance.")
    try:
        postgres_port = int(os.environ.get("SMOKE_POSTGRES_PORT", ""))
    except ValueError:
        postgres_port = 0
    if not 1 <= postgres_port <= 65535:
        raise SmokeFixtureError("Set SMOKE_POSTGRES_PORT to the loopback port of the disposable PostgreSQL instance.")

    check_redis(redis_url)
    service = f"uniquode-smoke-{uuid4().hex}"
    config = directory / "config.toml"
    write_config(config, service, postgres_port)
    values = build_secrets() | {
        "cache/redis/url": redis_url,
        "database/uniquode/service-account/user": "postgres",
        "database/uniquode/service-account/password": postgres_password,
        "database/uniquode/app/user": "uniquode_app",
        "database/uniquode/app/password": secrets.token_urlsafe(24),
    }
    if any(keyring.get_password(service, key) is not None for key in values):
        raise SmokeFixtureError("The generated smoke keychain service already contains credentials.")

    # Record the previously empty entries before seeding so partial writes are also cleaned up.
    manifest = directory / KEYCHAIN_MANIFEST
    manifest.write_text(json.dumps({"service": service, "keys": list(values)}), encoding="utf-8")
    if store_secrets(values, str(config)):
        raise SmokeFixtureError("Could not seed the smoke keychain service.")


def cleanup(directory: Path) -> None:
    manifest = json.loads((directory / KEYCHAIN_MANIFEST).read_text(encoding="utf-8"))
    service = manifest["service"]
    if not SMOKE_SERVICE.fullmatch(service):
        raise SmokeFixtureError("Refusing to clean up a keychain service outside the smoke namespace.")

    failures = 0
    for key in manifest["keys"]:
        try:
            if keyring.get_password(service, key) is not None:
                keyring.delete_password(service, key)
        except KeyringError:
            failures += 1
    if failures:
        raise SmokeFixtureError(f"Could not remove {failures} keychain entries from {service}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "cleanup"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "prepare":
            prepare(args.directory)
        else:
            cleanup(args.directory)
    except KeyringError:
        raise SystemExit("Cannot access the OS keychain for the smoke test.") from None
    except SmokeFixtureError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
