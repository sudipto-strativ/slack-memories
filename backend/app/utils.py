"""Utility functions for the Slack Trophy backend."""
from datetime import datetime, timedelta
from typing import Tuple


def parse_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """Parse ISO 8601 date strings and return datetime objects.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Tuple of (start_datetime, end_datetime)
    
    Raises:
        ValueError: If date format is invalid or range is too large
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD format. Error: {e}")
    
    if start > end:
        raise ValueError("Start date must be before end date")
    
    # Check date range limit (prevent DoS)
    max_range = timedelta(days=365)
    if (end - start) > max_range:
        raise ValueError(f"Date range cannot exceed {max_range.days} days")
    
    # Set end date to end of day
    end = end.replace(hour=23, minute=59, second=59)
    
    return start, end


def slack_timestamp_to_datetime(ts: str) -> datetime:
    """Convert Slack timestamp string to datetime object.
    
    Args:
        ts: Slack timestamp (e.g., "1234567890.000100")
    
    Returns:
        datetime object
    """
    try:
        timestamp = float(ts)
        return datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid Slack timestamp: {ts}")


def is_image_file(file_info: dict) -> bool:
    """Check if a Slack file is an image.
    
    Supports common image formats including:
    - JPEG, PNG, GIF, WebP
    - HEIC/HEIF (Apple formats)
    - TIFF, BMP, SVG
    - And other image formats
    
    Args:
        file_info: Slack file object
    
    Returns:
        True if file is an image, False otherwise
    """
    # Check mimetype field
    mime_type = file_info.get("mimetype", "").lower()
    if mime_type.startswith("image/"):
        return True
    
    # Check filetype field (alternative field Slack sometimes uses)
    file_type = file_info.get("filetype", "").lower()
    if file_type in ["jpg", "jpeg", "png", "gif", "webp", "heic", "heif", "tiff", "tif", "bmp", "svg", "ico", "avif"]:
        return True
    
    # Check pretty_type field
    pretty_type = file_info.get("pretty_type", "").lower()
    if "image" in pretty_type or pretty_type in ["jpg", "jpeg", "png", "gif", "webp", "heic", "heif"]:
        return True
    
    # Fallback: check file extension from name
    file_name = file_info.get("name", "").lower()
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".tiff", ".tif", ".bmp", ".svg", ".ico", ".avif"]
    if any(file_name.endswith(ext) for ext in image_extensions):
        return True
    
    return False


def is_video_file(file_info: dict) -> bool:
    """Check if a Slack file is a video.
    
    Supports common video formats including:
    - MP4, MOV, AVI, WebM, MKV
    - And other video formats
    
    Args:
        file_info: Slack file object
    
    Returns:
        True if file is a video, False otherwise
    """
    # Check mimetype field
    mime_type = file_info.get("mimetype", "").lower()
    if mime_type.startswith("video/"):
        return True
    
    # Check filetype field
    file_type = file_info.get("filetype", "").lower()
    if file_type in ["mp4", "mov", "avi", "webm", "mkv", "flv", "wmv", "m4v", "3gp", "ogv"]:
        return True
    
    # Check pretty_type field
    pretty_type = file_info.get("pretty_type", "").lower()
    if "video" in pretty_type or pretty_type in ["mp4", "mov", "avi", "webm", "mkv"]:
        return True
    
    # Fallback: check file extension from name
    file_name = file_info.get("name", "").lower()
    video_extensions = [".mp4", ".mov", ".avi", ".webm", ".mkv", ".flv", ".wmv", ".m4v", ".3gp", ".ogv"]
    if any(file_name.endswith(ext) for ext in video_extensions):
        return True
    
    return False


def get_media_type(file_info: dict) -> str:
    """Get the media type of a Slack file.
    
    Args:
        file_info: Slack file object
    
    Returns:
        "image", "video", or "unknown"
    """
    if is_image_file(file_info):
        return "image"
    elif is_video_file(file_info):
        return "video"
    return "unknown"


def validate_channel_id(channel_id: str) -> None:
    """Validate Slack channel ID format.
    
    Args:
        channel_id: Channel ID to validate
    
    Raises:
        ValueError: If channel ID format is invalid
    """
    if not channel_id:
        raise ValueError("Channel ID is required")
    
    # Slack channel IDs start with C (public) or G (private group)
    if not (channel_id.startswith("C") or channel_id.startswith("G")):
        raise ValueError("Invalid channel ID format")

