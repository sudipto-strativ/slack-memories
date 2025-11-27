"""Slack API client wrapper for the Slack Trophy backend."""
from datetime import datetime
from typing import List, Dict, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .config import settings
from .models import Channel, Photo, Message
from .utils import (
    parse_date_range,
    slack_timestamp_to_datetime,
    is_image_file,
    is_video_file,
    get_media_type,
    validate_channel_id
)


class SlackClient:
    """Wrapper for Slack Web API client."""
    
    def __init__(self):
        """Initialize Slack client with user token."""
        self.client = WebClient(token=settings.SLACK_USER_TOKEN)
    
    def get_channels(self) -> List[Channel]:
        """Fetch channels that match specific keywords.
        
        Returns:
            List of Channel objects (only channels containing allowed keywords)
        
        Raises:
            SlackApiError: If Slack API call fails
        """
        channels = []
        
        # Keywords to include - only channels containing these will be shown
        allowed_keywords = ["general", "privatekotha", "internal-development"]
        
        def should_include_channel(channel_name: str) -> bool:
            """Check if channel should be included (contains one of the allowed keywords)."""
            channel_name_lower = channel_name.lower()
            return any(keyword.lower() in channel_name_lower for keyword in allowed_keywords)
        
        try:
            # Fetch public channels
            public_response = self.client.conversations_list(
                types="public_channel",
                exclude_archived=True
            )
            
            for channel_data in public_response.get("channels", []):
                channel_name = channel_data.get("name", "")
                if should_include_channel(channel_name):
                    channels.append(Channel(
                        id=channel_data["id"],
                        name=channel_name,
                        is_private=False
                    ))
            
            # Fetch private channels/groups
            private_response = self.client.conversations_list(
                types="private_channel",
                exclude_archived=True
            )
            
            for channel_data in private_response.get("channels", []):
                channel_name = channel_data.get("name", "")
                if should_include_channel(channel_name):
                    channels.append(Channel(
                        id=channel_data["id"],
                        name=channel_name,
                        is_private=True
                    ))
        
        except SlackApiError as e:
            # Re-raise the original exception - let the caller handle it
            raise
        
        return channels
    
    def get_channel_history(
        self,
        channel_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """Fetch messages from a channel within a date range.
        
        Args:
            channel_id: Slack channel ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            List of message dictionaries
        
        Raises:
            SlackApiError: If Slack API call fails
        """
        validate_channel_id(channel_id)
        start_dt, end_dt = parse_date_range(start_date, end_date)
        
        # Convert to Slack timestamps
        start_ts = str(start_dt.timestamp())
        end_ts = str(end_dt.timestamp())
        
        all_messages = []
        cursor = None
        
        try:
            while True:
                response = self.client.conversations_history(
                    channel=channel_id,
                    oldest=start_ts,
                    latest=end_ts,
                    cursor=cursor,
                    limit=200,  # Maximum allowed by Slack API
                    include_all_metadata=True  # Include file metadata
                )
                
                messages = response.get("messages", [])
                all_messages.extend(messages)
                
                # Check if there are more pages
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        
        except SlackApiError as e:
            # Re-raise the original exception - let the caller handle it
            raise
        
        return all_messages
    
    def extract_photos(
        self,
        messages: List[Dict],
        channel_id: str = None,
        unique_reactions: bool = False,
        debug: bool = False
    ) -> List[Photo]:
        """Extract photos and videos from messages and count reactions.
        
        Args:
            messages: List of message dictionaries from Slack
            unique_reactions: If True, count only unique users per emoji
            debug: If True, print debug information about skipped messages
        
        Returns:
            List of Photo objects (images and videos) sorted by total_reactions (descending)
        """
        photos = []
        skipped_stats = {
            "thread_messages": 0,
            "no_files": 0,
            "no_media_files": 0,
            "no_url": 0,
            "unknown_type": 0,
            "processed": 0
        }
        
        for msg in messages:
            # Skip thread messages
            # if msg.get("thread_ts"):
            #     skipped_stats["thread_messages"] += 1
            #     if debug:
            #         print(f"DEBUG: Skipping thread message {msg.get('ts')}")
            #     continue
            
            # Check for files in multiple locations
            files = msg.get("files", [])
            
            # Also check attachments for files
            attachments = msg.get("attachments", [])
            for attachment in attachments:
                # Some attachments have image_url or thumb_url
                if attachment.get("image_url"):
                    # Create a pseudo-file object for image_url attachments
                    files.append({
                        "url_private": attachment.get("image_url"),
                        "mimetype": "image/jpeg",  # Default assumption
                        "name": attachment.get("title", "image"),
                        "permalink": attachment.get("image_url")
                    })
                # Check if attachment has files
                if attachment.get("files"):
                    files.extend(attachment.get("files", []))
            
            # Check blocks for images
            blocks = msg.get("blocks", [])
            for block in blocks:
                if block.get("type") == "image" and block.get("image_url"):
                    files.append({
                        "url_private": block.get("image_url"),
                        "mimetype": "image/jpeg",
                        "name": "block_image",
                        "permalink": block.get("image_url")
                    })
            
            if not files:
                skipped_stats["no_files"] += 1
                if debug:
                    print(f"DEBUG: Message {msg.get('ts')} has no files. Keys: {list(msg.keys())}")
                continue
            
            # Find image and video files
            media_files = [f for f in files if is_image_file(f) or is_video_file(f)]
            if not media_files:
                skipped_stats["no_media_files"] += 1
                if debug:
                    file_types = [f.get("mimetype", "unknown") for f in files[:3]]
                    print(f"DEBUG: Message {msg.get('ts')} has {len(files)} files but none are media. Types: {file_types}")
                continue
            
            # Use the first media file (image or video)
            media_file = media_files[0]
            
            # Get file permalink (prefer url_private, then thumb_1024, then permalink)
            file_url = (
                media_file.get("url_private") or 
                media_file.get("thumb_1024") or 
                media_file.get("thumb_960") or
                media_file.get("thumb_720") or
                media_file.get("permalink", "")
            )
            if not file_url:
                skipped_stats["no_url"] += 1
                if debug:
                    print(f"DEBUG: Message {msg.get('ts')} media file has no URL. File keys: {list(media_file.keys())}")
                continue
            
            # Determine media type
            media_type = get_media_type(media_file)
            if media_type == "unknown":
                skipped_stats["unknown_type"] += 1
                if debug:
                    print(f"DEBUG: Message {msg.get('ts')} media type is unknown. mimetype: {media_file.get('mimetype')}, filetype: {media_file.get('filetype')}")
                continue
            
            # Extract reactions
            emoji_reactions = self._count_reactions(
                msg.get("reactions", []),
                unique_reactions
            )
            
            # Calculate total reactions
            if unique_reactions and "__total_unique_people__" in emoji_reactions:
                # For unique reactions, use the total unique people count
                total_reactions = emoji_reactions.pop("__total_unique_people__")
            else:
                # For non-unique reactions, sum all emoji counts
                total_reactions = sum(emoji_reactions.values())
            
            # Skip photos with 0 reactions
            if total_reactions == 0:
                skipped_stats["no_reactions"] = skipped_stats.get("no_reactions", 0) + 1
                if debug:
                    print(f"DEBUG: Skipping photo {msg.get('ts')} with 0 reactions")
                continue
            
            # Get uploader name
            uploader_name = None
            if msg.get("user"):
                try:
                    user_info = self.client.users_info(user=msg["user"])
                    uploader_name = user_info.get("user", {}).get("name")
                except SlackApiError:
                    pass  # Skip if user lookup fails
            
            # Use channel_id from parameter, fallback to message channel field
            photo_channel_id = channel_id or msg.get("channel", "")
            
            photo = Photo(
                id=msg["ts"],
                url=file_url,
                channel_id=photo_channel_id,
                timestamp=msg["ts"],
                uploader_name=uploader_name,
                emoji_reactions=emoji_reactions,
                total_reactions=total_reactions,
                media_type=media_type
            )
            
            photos.append(photo)
            skipped_stats["processed"] += 1
        
        if debug:
            print(f"\nDEBUG STATS:")
            print(f"  Processed: {skipped_stats['processed']}")
            print(f"  Skipped - Threads: {skipped_stats['thread_messages']}")
            print(f"  Skipped - No files: {skipped_stats['no_files']}")
            print(f"  Skipped - No media files: {skipped_stats['no_media_files']}")
            print(f"  Skipped - No URL: {skipped_stats['no_url']}")
            print(f"  Skipped - Unknown type: {skipped_stats['unknown_type']}")
            print(f"  Skipped - No reactions: {skipped_stats.get('no_reactions', 0)}")
            print(f"  Total photos found: {len(photos)}\n")
        
        # Sort by total reactions (descending)
        photos.sort(key=lambda x: x.total_reactions, reverse=True)
        
        # Assign ranks
        for idx, photo in enumerate(photos, start=1):
            photo.rank = idx
        
        return photos
    
    def update_photo_reactions(
        self,
        photos: List[Photo],
        messages: List[Dict],
        unique_reactions: bool = False
    ) -> List[Photo]:
        """Update reactions for photos from fresh messages.
        
        This is used to refresh reaction counts for cached photos.
        
        Args:
            photos: List of Photo objects (from cache)
            messages: Fresh list of message dictionaries from Slack
            unique_reactions: If True, count only unique people
        
        Returns:
            Updated list of Photo objects with fresh reactions, sorted by total_reactions
        """
        # Create a mapping of timestamp -> message for quick lookup
        message_map = {msg.get("ts"): msg for msg in messages}
        
        # Update reactions for each photo and filter out photos with 0 reactions
        updated_photos = []
        for photo in photos:
            msg = message_map.get(photo.timestamp)
            if msg:
                # Extract fresh reactions
                emoji_reactions = self._count_reactions(
                    msg.get("reactions", []),
                    unique_reactions
                )
                
                # Calculate total reactions
                if unique_reactions and "__total_unique_people__" in emoji_reactions:
                    total_reactions = emoji_reactions.pop("__total_unique_people__")
                else:
                    total_reactions = sum(emoji_reactions.values())
                
                # Skip photos with 0 reactions
                if total_reactions == 0:
                    continue
                
                # Update photo with fresh reactions
                photo.emoji_reactions = emoji_reactions
                photo.total_reactions = total_reactions
                updated_photos.append(photo)
        
        # Re-sort by total reactions (descending)
        updated_photos.sort(key=lambda x: x.total_reactions, reverse=True)
        
        # Re-assign ranks
        for idx, photo in enumerate(updated_photos, start=1):
            photo.rank = idx
        
        return updated_photos
    
    def update_message_reactions(
        self,
        messages_list: List[Message],
        messages: List[Dict],
        unique_reactions: bool = False
    ) -> List[Message]:
        """Update reactions for messages from fresh message data.
        
        This is used to refresh reaction counts for cached messages.
        
        Args:
            messages_list: List of Message objects (from cache)
            messages: Fresh list of message dictionaries from Slack
            unique_reactions: If True, count only unique people
        
        Returns:
            Updated list of Message objects with fresh reactions, sorted by total_reactions
        """
        # Create a mapping of timestamp -> message for quick lookup
        message_map = {msg.get("ts"): msg for msg in messages}
        
        # Update reactions for each message
        for cached_msg in messages_list:
            msg = message_map.get(cached_msg.timestamp)
            if msg:
                # Extract fresh reactions
                emoji_reactions = self._count_reactions(
                    msg.get("reactions", []),
                    unique_reactions
                )
                
                # Calculate total reactions
                if unique_reactions and "__total_unique_people__" in emoji_reactions:
                    total_reactions = emoji_reactions.pop("__total_unique_people__")
                else:
                    total_reactions = sum(emoji_reactions.values())
                
                # Update message with fresh reactions
                cached_msg.emoji_reactions = emoji_reactions
                cached_msg.total_reactions = total_reactions
        
        # Re-sort by total reactions (descending)
        messages_list.sort(key=lambda x: x.total_reactions, reverse=True)
        
        # Re-assign ranks
        for idx, msg in enumerate(messages_list, start=1):
            msg.rank = idx
        
        return messages_list
    
    def extract_messages(
        self,
        messages: List[Dict],
        unique_reactions: bool = False
    ) -> List[Message]:
        """Extract text messages (without attachments) and count reactions.
        
        Args:
            messages: List of message dictionaries from Slack
            unique_reactions: If True, count only unique users per emoji
        
        Returns:
            List of Message objects sorted by total_reactions (descending)
        """
        extracted_messages = []
        
        for msg in messages:
            # Skip thread messages
            if msg.get("thread_ts"):
                continue
            
            # Skip messages with files/attachments
            if msg.get("files") or msg.get("attachments"):
                continue
            
            # Skip empty messages
            text = msg.get("text", "").strip()
            if not text:
                continue
            
            # Extract reactions
            emoji_reactions = self._count_reactions(
                msg.get("reactions", []),
                unique_reactions
            )
            
            # Calculate total reactions
            if unique_reactions and "__total_unique_people__" in emoji_reactions:
                # For unique reactions, use the total unique people count
                total_reactions = emoji_reactions.pop("__total_unique_people__")
            else:
                # For non-unique reactions, sum all emoji counts
                total_reactions = sum(emoji_reactions.values())
            
            # Get author name
            author_name = None
            if msg.get("user"):
                try:
                    user_info = self.client.users_info(user=msg["user"])
                    author_name = user_info.get("user", {}).get("name")
                except SlackApiError:
                    pass  # Skip if user lookup fails
            
            message = Message(
                id=msg["ts"],
                text=text,
                author_name=author_name,
                channel_id=msg.get("channel", ""),
                timestamp=msg["ts"],
                emoji_reactions=emoji_reactions,
                total_reactions=total_reactions
            )
            
            extracted_messages.append(message)
        
        # Sort by total reactions (descending)
        extracted_messages.sort(key=lambda x: x.total_reactions, reverse=True)
        
        # Assign ranks
        for idx, message in enumerate(extracted_messages, start=1):
            message.rank = idx
        
        return extracted_messages
    
    def _count_reactions(
        self,
        reactions: List[Dict],
        unique_reactions: bool = False
    ) -> Dict[str, int]:
        """Count emoji reactions from message reactions.
        
        Args:
            reactions: List of reaction dictionaries from Slack
            unique_reactions: If True, count only unique people (one person = one count, regardless of emoji count)
        
        Returns:
            Dictionary mapping emoji to count
        """
        emoji_counts: Dict[str, int] = {}
        
        if not reactions:
            return emoji_counts
        
        if unique_reactions:
            # Count unique people across all reactions
            # Collect all unique users who reacted (regardless of which emoji)
            all_unique_users = set()
            for reaction in reactions:
                users = reaction.get("users", [])
                all_unique_users.update(users)
            
            # Total unique people count
            total_unique_people = len(all_unique_users)
            
            # For each emoji, show how many unique people reacted with that emoji
            # But the total_reactions will be the count of unique people overall
            for reaction in reactions:
                emoji = reaction.get("name", "")
                users = reaction.get("users", [])
                # Count unique users for this emoji
                unique_user_count = len(set(users))
                emoji_counts[emoji] = unique_user_count
            
            # Store total unique people count in a special key for later use
            # We'll use this to override total_reactions calculation
            emoji_counts["__total_unique_people__"] = total_unique_people
        else:
            # Count all reactions (users can react multiple times)
            for reaction in reactions:
                emoji = reaction.get("name", "")
                count = reaction.get("count", 0)
                emoji_counts[emoji] = count
        
        return emoji_counts


# Global Slack client instance
slack_client = SlackClient()

