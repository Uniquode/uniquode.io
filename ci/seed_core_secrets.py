#!/usr/bin/env python3
"""Generate and seed the core application secrets needed by CI.

Both the "tests" job (`.github/workflows/tests.yml`) and `smoke_test.sh`
need to seed the same set of core app secrets (signing key, CSRF secret,
OAuth client secrets, Apple private key) into the keychain before the app
will boot. This used to be duplicated inline in both places; keeping it in
one script means a new required secret only needs to be added once, instead
of the two copies silently drifting apart.

The generated secrets are piped directly into `wybra-secret set --json` via
its stdin, without ever being printed to stdout/stderr -- this keeps them
out of CI logs and avoids the "clear-text logging of sensitive information"
class of static-analysis findings.

Usage:
    uv run python ci/seed_core_secrets.py [--config PATH]
"""

from __future__ import annotations

import argparse
import base64
import json
import secrets
import subprocess
import sys
import zlib

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def build_secrets() -> dict[str, str]:
    encoded_key = Fernet.generate_key().decode("ascii")
    raw_key = base64.urlsafe_b64decode(encoded_key)
    checksum = f"{zlib.crc32(raw_key) & 0xFFFFFFFF:08x}"
    apple_private_key = ec.generate_private_key(ec.SECP256R1())
    apple_private_key_pem = apple_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    return {
        "secrets/key/current": f"ci:{encoded_key}:{checksum}",
        "auth/forms/csrf-token-secret/current": secrets.token_urlsafe(32),
        "auth/providers/google/client-secret": secrets.token_urlsafe(32),
        "auth/providers/github/client-secret": secrets.token_urlsafe(32),
        "auth/providers/apple/private-key": apple_private_key_pem,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed core app secrets into the keychain via wybra-secret.",
    )
    parser.add_argument(
        "--config",
        help="Forwarded as wybra-secret's --config flag, if provided.",
    )
    args = parser.parse_args(argv)

    payload = json.dumps(build_secrets()).encode("utf-8")

    command = ["uv", "run", "wybra-secret"]
    if args.config:
        command += ["--config", args.config]
    command += ["set", "--json"]

    result = subprocess.run(command, input=payload)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
