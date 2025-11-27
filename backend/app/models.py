"""Pydantic models for API requests and responses."""
from typing import Dict, Optional
from pydantic import BaseModel, Field


class Channel(BaseModel):
    """Slack channel model."""
    id: str
    name: str
    is_private: bool = False


class ChannelsResponse(BaseModel):
    """Response model for channels endpoint."""
    channels: list[Channel]


class EmojiReactions(BaseModel):
    """Emoji reactions dictionary."""
    reactions: Dict[str, int] = Field(default_factory=dict)


class Photo(BaseModel):
    """Photo/Video model with emoji reactions."""
    id: str
    url: str
    channel_id: str
    timestamp: str
    uploader_name: Optional[str] = None
    emoji_reactions: Dict[str, int] = Field(default_factory=dict)
    total_reactions: int = 0
    rank: Optional[int] = None
    media_type: str = "image"  # "image" or "video"


class Message(BaseModel):
    """Message model with emoji reactions."""
    id: str
    text: str
    author_name: Optional[str] = None
    channel_id: str
    timestamp: str
    emoji_reactions: Dict[str, int] = Field(default_factory=dict)
    total_reactions: int = 0
    rank: Optional[int] = None


class PhotosResponse(BaseModel):
    """Response model for photos endpoint."""
    items: list[Photo]


class MessagesResponse(BaseModel):
    """Response model for messages endpoint."""
    items: list[Message]


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "ok"

