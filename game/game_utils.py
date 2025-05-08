# game/game_utils.py

import base64
from typing import Any

def clip_to_base64(path: str) -> str:
    """
    Reads the file at `path` in binary mode and returns
    a Base64‑encoded ASCII string suitable for JSON transport.
    """
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("ascii")