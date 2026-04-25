from __future__ import annotations

import os
import re
from urllib.parse import parse_qs, unquote, urlparse

import requests


FIGMA_API_BASE_URL = "https://api.figma.com/v1"


class FigmaClient:
    def __init__(self) -> None:
        self.access_token = os.getenv("FIGMA_ACCESS_TOKEN", "")
        self.base_url = os.getenv("FIGMA_API_BASE_URL", FIGMA_API_BASE_URL)
        self.timeout = float(os.getenv("FIGMA_TIMEOUT_SECONDS", "60"))

        if not self.access_token:
            raise ValueError("FIGMA_ACCESS_TOKEN is required to read Figma files.")

    def get_file(self, file_key: str, node_id: str = "") -> dict:
        params = {}
        if node_id:
            params["ids"] = node_id

        response = requests.get(
            f"{self.base_url.rstrip('/')}/files/{file_key}",
            headers={"X-Figma-Token": self.access_token},
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_image_urls(self, file_key: str, node_ids: list[str]) -> dict[str, str]:
        if not node_ids:
            return {}

        response = requests.get(
            f"{self.base_url.rstrip('/')}/images/{file_key}",
            headers={"X-Figma-Token": self.access_token},
            params={"ids": ",".join(node_ids), "format": "png", "scale": "1"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            node_id: image_url or ""
            for node_id, image_url in payload.get("images", {}).items()
        }


def parse_figma_url(figma_url: str) -> tuple[str, str]:
    parsed = urlparse(figma_url)
    path_parts = [part for part in parsed.path.split("/") if part]

    file_key = ""
    for idx, part in enumerate(path_parts):
        if part in {"file", "design", "proto"} and idx + 1 < len(path_parts):
            file_key = path_parts[idx + 1]
            break

    if not file_key and path_parts:
        file_key = path_parts[0]

    query = parse_qs(parsed.query)
    raw_node_id = query.get("node-id", [""])[0]
    node_id = unquote(raw_node_id).replace("-", ":")

    if not file_key or not re.match(r"^[A-Za-z0-9]+$", file_key):
        raise ValueError("Invalid Figma URL: file key not found.")

    return file_key, node_id
