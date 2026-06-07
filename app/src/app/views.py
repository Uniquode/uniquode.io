from typing import Any

from fastapi import Request


def build_home_context(_request: Request) -> dict[str, Any]:
    return {
        "page_title": "uniquode",
    }
