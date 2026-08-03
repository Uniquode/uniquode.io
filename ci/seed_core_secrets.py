#!/usr/bin/env python3
"""Generate the core application secrets seeded by CI.

Both the "tests" job (`.github/workflows/tests.yml`) and `smoke_test.sh`
need to seed the same set of core app secrets (signing key, CSRF secret,
OAuth client secrets, Apple private key) into the keychain before the app
will boot. This used to be duplicated inline in both places; keeping it in
one script means a new required secret only needs to be added once, instead
of the two copies silently drifting apart.

Usage: `uv run python ci/seed_core_secrets.py | uv run wybra-secret set --json`
"""

from __future__ import annotations

import base64
import json
import secrets
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


def main() -> int:
    print(json.dumps(build_secrets()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
