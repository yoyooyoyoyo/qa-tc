from __future__ import annotations

from pydantic import BaseModel, Field


class FigmaScreen(BaseModel):
    node_id: str = Field(..., description="Figma node id")
    name: str = Field(..., description="화면/frame 이름")
    path: str = Field(default="", description="페이지/섹션/frame 경로")
    node_type: str = Field(default="", description="Figma node type")
    text_layers: list[str] = Field(default_factory=list, description="하위 텍스트 레이어")
    image_url: str = Field(default="", description="렌더링 이미지 URL")


class FigmaContext(BaseModel):
    file_key: str
    node_id: str = ""
    file_name: str = ""
    screens: list[FigmaScreen] = Field(default_factory=list)


class ExtractFigmaContextRequest(BaseModel):
    figma_url: str
    include_images: bool = Field(default=False)
    max_screens: int = Field(default=30, ge=1, le=100)


class ExtractFigmaContextResponse(BaseModel):
    message: str
    context: FigmaContext
