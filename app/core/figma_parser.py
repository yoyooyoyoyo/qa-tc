from __future__ import annotations

from app.core.figma_client import FigmaClient, parse_figma_url
from app.schemas.figma import FigmaContext, FigmaScreen


SCREEN_NODE_TYPES = {"FRAME", "SECTION", "COMPONENT", "INSTANCE"}
TEXT_NODE_TYPE = "TEXT"


def extract_figma_context(
    figma_url: str,
    *,
    include_images: bool = False,
    max_screens: int = 30,
    figma_client: FigmaClient | None = None,
) -> FigmaContext:
    file_key, node_id = parse_figma_url(figma_url)
    client = figma_client or FigmaClient()
    payload = client.get_file(file_key, node_id=node_id)
    document = payload.get("document", {})

    screens = _collect_screens(document, max_screens=max_screens)

    if include_images:
        image_urls = client.get_image_urls(
            file_key,
            [screen.node_id for screen in screens],
        )
        for screen in screens:
            screen.image_url = image_urls.get(screen.node_id, "")

    return FigmaContext(
        file_key=file_key,
        node_id=node_id,
        file_name=payload.get("name", ""),
        screens=screens,
    )


def figma_context_to_prompt_text(context: FigmaContext) -> str:
    if not context.screens:
        return ""

    lines = [
        f"Figma file: {context.file_name or context.file_key}",
        f"Figma node: {context.node_id or 'all'}",
        "",
        "Screens:",
    ]

    for screen in context.screens:
        lines.append(f"- {screen.path or screen.name}")
        if screen.text_layers:
            joined_texts = " / ".join(screen.text_layers[:20])
            lines.append(f"  texts: {joined_texts}")

    return "\n".join(lines)


def _collect_screens(node: dict, *, max_screens: int) -> list[FigmaScreen]:
    screens: list[FigmaScreen] = []

    def walk(current: dict, ancestors: list[str]) -> None:
        if len(screens) >= max_screens:
            return

        node_type = current.get("type", "")
        node_name = current.get("name", "")
        current_path = [*ancestors, node_name] if node_name else ancestors

        if node_type in SCREEN_NODE_TYPES and _is_screen_like(current):
            screens.append(
                FigmaScreen(
                    node_id=current.get("id", ""),
                    name=node_name,
                    path=" > ".join([part for part in current_path if part]),
                    node_type=node_type,
                    text_layers=_collect_text_layers(current),
                )
            )

        for child in current.get("children", []):
            walk(child, current_path)

    walk(node, [])
    return screens


def _is_screen_like(node: dict) -> bool:
    if node.get("visible") is False:
        return False

    node_name = node.get("name", "").strip()
    if not node_name:
        return False

    bounds = node.get("absoluteBoundingBox") or {}
    width = bounds.get("width", 0) or 0
    height = bounds.get("height", 0) or 0

    if width >= 240 and height >= 240:
        return True

    return node.get("type") == "SECTION"


def _collect_text_layers(node: dict) -> list[str]:
    texts: list[str] = []

    def walk(current: dict) -> None:
        if len(texts) >= 80:
            return

        if current.get("visible") is False:
            return

        if current.get("type") == TEXT_NODE_TYPE:
            text = current.get("characters", "").strip()
            if text:
                texts.append(text)

        for child in current.get("children", []):
            walk(child)

    walk(node)
    return _dedupe(texts)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = " ".join(value.split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)

    return deduped
