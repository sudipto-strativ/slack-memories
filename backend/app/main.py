"""FastAPI application for Slack Trophy backend."""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
from slack_sdk.errors import SlackApiError

from .config import settings
from .models import (
    ChannelsResponse,
    PhotosResponse,
    MessagesResponse,
    HealthResponse
)
from .slack_client import slack_client
from .cache import cache
from .utils import validate_channel_id, parse_date_range

# Validate settings on startup
try:
    settings.validate()
except ValueError as e:
    print(f"Warning: Configuration validation failed: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Slack Memories API",
    description="API for aggregating and displaying top-rated Slack photos and messages",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.get("/channels", response_model=ChannelsResponse)
async def get_channels():
    """Get list of available Slack channels.
    
    Returns:
        List of channels the bot has access to
    """
    try:
        # Check cache first
        cache_key = "channels"
        cached_channels = cache.get(cache_key)
        if cached_channels is not None:
            return ChannelsResponse(channels=cached_channels)
        
        # Fetch from Slack
        channels = slack_client.get_channels()
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, channels, ttl=3600)
        
        return ChannelsResponse(channels=channels)
    
    except SlackApiError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response:
            error_detail = e.response.get('error', error_detail)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch channels: {error_detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.get("/photos", response_model=PhotosResponse)
async def get_photos(
    channel_id: str = Query(..., description="Slack channel ID"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    unique_reactions: bool = Query(False, description="Count only unique reactions per user"),
    debug: bool = Query(False, description="Enable debug logging")
):
    """Get photos from a channel within a date range, sorted by reaction count.
    
    Args:
        channel_id: Slack channel ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        unique_reactions: If True, count only unique users per emoji
    
    Returns:
        List of photos sorted by total reactions (descending)
    """
    try:
        # Validate inputs
        validate_channel_id(channel_id)
        parse_date_range(start_date, end_date)
        
        # Check cache for photos (metadata only, reactions will be refreshed)
        cache_key = cache.generate_key(
            channel_id, start_date, end_date, unique_reactions, "photos"
        )
        cached_photos = cache.get(cache_key)
        
        # Always fetch fresh messages to get latest reactions
        # (Messages can be cached separately if needed, but for now we fetch fresh)
        messages = slack_client.get_channel_history(channel_id, start_date, end_date)
        
        if cached_photos is not None:
            # Update reactions for cached photos with fresh data
            photos = slack_client.update_photo_reactions(
                cached_photos, messages, unique_reactions
            )
        else:
            # Extract photos from messages (first time)
            photos = slack_client.extract_photos(messages, unique_reactions, debug=debug)
            # Cache results (photos metadata, reactions will be refreshed next time)
            cache.set(cache_key, photos, ttl=settings.CACHE_TTL)
        
        return PhotosResponse(items=photos)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SlackApiError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response:
            error_detail = e.response.get('error', error_detail)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch photos: {error_detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.get("/messages", response_model=MessagesResponse)
async def get_messages(
    channel_id: str = Query(..., description="Slack channel ID"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    unique_reactions: bool = Query(False, description="Count only unique reactions per user")
):
    """Get text messages from a channel within a date range, sorted by reaction count.
    
    Args:
        channel_id: Slack channel ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        unique_reactions: If True, count only unique users per emoji
    
    Returns:
        List of messages sorted by total reactions (descending)
    """
    try:
        # Validate inputs
        validate_channel_id(channel_id)
        parse_date_range(start_date, end_date)
        
        # Check cache for messages (metadata only, reactions will be refreshed)
        cache_key = cache.generate_key(
            channel_id, start_date, end_date, unique_reactions, "messages"
        )
        cached_messages = cache.get(cache_key)
        
        # Always fetch fresh messages to get latest reactions
        messages = slack_client.get_channel_history(channel_id, start_date, end_date)
        
        if cached_messages is not None:
            # Update reactions for cached messages with fresh data
            extracted_messages = slack_client.update_message_reactions(
                cached_messages, messages, unique_reactions
            )
        else:
            # Extract text messages from messages (first time)
            extracted_messages = slack_client.extract_messages(messages, unique_reactions)
            # Cache results (message metadata, reactions will be refreshed next time)
            cache.set(cache_key, extracted_messages, ttl=settings.CACHE_TTL)
        
        return MessagesResponse(items=extracted_messages)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SlackApiError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response:
            error_detail = e.response.get('error', error_detail)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch messages: {error_detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.get("/proxy-image")
async def proxy_image(url: str = Query(..., description="Image or video URL to proxy")):
    """Proxy Slack images and videos with authentication headers.
    
    Args:
        url: Slack image or video URL to proxy
    
    Returns:
        Media stream with proper headers
    """
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.SLACK_USER_TOKEN}"
            }
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Get content type from response, default based on URL if not available
            content_type = response.headers.get("content-type")
            if not content_type:
                # Try to infer from URL
                if any(url.lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']):
                    content_type = "video/mp4"
                else:
                    content_type = "image/jpeg"
            
            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to proxy media: {str(e)}"
        )


@app.get("/debug/messages")
async def debug_messages(
    channel_id: str = Query(..., description="Slack channel ID"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    limit: int = Query(10, description="Number of messages to return")
):
    """Debug endpoint to inspect raw message data and see what files are present.
    
    This helps identify why some photos might be missing.
    """
    try:
        validate_channel_id(channel_id)
        parse_date_range(start_date, end_date)
        
        # Fetch messages from Slack
        messages = slack_client.get_channel_history(channel_id, start_date, end_date)
        
        # Analyze first N messages
        debug_info = []
        for msg in messages[:limit]:
            msg_info = {
                "ts": msg.get("ts"),
                "user": msg.get("user"),
                "is_thread": bool(msg.get("thread_ts")),
                "has_files": bool(msg.get("files")),
                "has_attachments": bool(msg.get("attachments")),
                "has_blocks": bool(msg.get("blocks")),
                "file_count": len(msg.get("files", [])),
                "files": []
            }
            
            # Analyze files
            for f in msg.get("files", [])[:3]:  # First 3 files
                msg_info["files"].append({
                    "name": f.get("name"),
                    "mimetype": f.get("mimetype"),
                    "filetype": f.get("filetype"),
                    "pretty_type": f.get("pretty_type"),
                    "has_url_private": bool(f.get("url_private")),
                    "has_thumb_1024": bool(f.get("thumb_1024")),
                    "has_permalink": bool(f.get("permalink")),
                    "keys": list(f.keys())[:10]  # First 10 keys
                })
            
            # Check attachments
            if msg.get("attachments"):
                msg_info["attachments"] = []
                for att in msg.get("attachments", [])[:2]:
                    msg_info["attachments"].append({
                        "has_image_url": bool(att.get("image_url")),
                        "has_thumb_url": bool(att.get("thumb_url")),
                        "has_files": bool(att.get("files")),
                        "keys": list(att.keys())[:10]
                    })
            
            debug_info.append(msg_info)
        
        return {
            "total_messages": len(messages),
            "analyzed": len(debug_info),
            "messages": debug_info
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Debug error: {str(e)}"
        )


@app.get("/emoji-info")
async def get_emoji_info(emoji_name: str = Query(..., description="Emoji name (e.g., 'custom_emoji' or ':+1:')")):
    """Get emoji image URL for custom Slack emojis.
    
    Args:
        emoji_name: Emoji name (with or without colons)
    
    Returns:
        Emoji image URL or null if not found
    """
    try:
        # Remove colons if present
        emoji_name = emoji_name.strip(':')
        
        # Get team info to construct emoji URL
        team_info = slack_client.client.team_info()
        team_id = team_info.get("team", {}).get("id", "")
        
        if not team_id:
            return {"url": None, "is_custom": False}
        
        # Try to get emoji info from Slack
        try:
            emoji_list = slack_client.client.emoji_list()
            emojis = emoji_list.get("emoji", {})
            
            if emoji_name in emojis:
                emoji_url = emojis[emoji_name]
                # If it's a custom emoji, it will be a URL
                if emoji_url.startswith("http"):
                    return {"url": emoji_url, "is_custom": True}
                # If it's an alias, follow it
                elif emoji_url.startswith(":"):
                    alias_name = emoji_url.strip(':')
                    if alias_name in emojis:
                        alias_url = emojis[alias_name]
                        if alias_url.startswith("http"):
                            return {"url": alias_url, "is_custom": True}
        except SlackApiError:
            pass
        
        # If not found in emoji list, construct URL (Slack's emoji CDN pattern)
        # Format: https://emoji.slack-edge.com/T{TEAM_ID}/{emoji_name}/{hash}.png
        # We can't get the hash without the API, so return None
        return {"url": None, "is_custom": False}
    
    except Exception as e:
        return {"url": None, "is_custom": False, "error": str(e)}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

