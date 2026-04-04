"""
Discord Platform - Data Models
===============================

Discord-specific data models and message types.

Discord Concepts:
-----------------
- Guild: A Discord server
- Channel: Where messages are sent (text, voice, etc.)
- User: Discord user
- Message: Text message, embed, file, etc.
- Interaction: Button clicks, slash commands
- Embed: Rich formatted message

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 6
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# DISCORD USER
# ============================================

class DiscordUser(BaseModel):
    """
    Discord user model.
    
    Represents a Discord user or bot.
    """
    id: str = Field(..., description="Discord user ID (snowflake)")
    username: str = Field(..., description="User's username")
    discriminator: str = Field(..., description="4-digit discriminator (e.g., '0001')")
    avatar: Optional[str] = Field(None, description="Avatar hash")
    bot: Optional[bool] = Field(False, description="Whether user is a bot")
    system: Optional[bool] = Field(False, description="Whether user is system")
    
    def get_tag(self) -> str:
        """Get user tag (username#discriminator)."""
        return f"{self.username}#{self.discriminator}"
    
    def get_mention(self) -> str:
        """Get mention string (<@user_id>)."""
        return f"<@{self.id}>"
    
    def get_avatar_url(self) -> Optional[str]:
        """Get avatar URL."""
        if self.avatar:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        return None


# ============================================
# DISCORD GUILD (SERVER)
# ============================================

class DiscordGuild(BaseModel):
    """
    Discord guild (server) model.
    """
    id: str = Field(..., description="Guild ID (snowflake)")
    name: str = Field(..., description="Guild name")
    icon: Optional[str] = Field(None, description="Icon hash")
    owner_id: Optional[str] = Field(None, description="Owner's user ID")
    member_count: Optional[int] = Field(None, description="Number of members")


# ============================================
# DISCORD CHANNEL
# ============================================

class DiscordChannel(BaseModel):
    """
    Discord channel model.
    """
    id: str = Field(..., description="Channel ID (snowflake)")
    type: int = Field(..., description="Channel type (0=text, 2=voice, etc.)")
    guild_id: Optional[str] = Field(None, description="Guild ID")
    name: Optional[str] = Field(None, description="Channel name")
    topic: Optional[str] = Field(None, description="Channel topic")
    
    def is_text_channel(self) -> bool:
        """Check if this is a text channel."""
        return self.type == 0
    
    def is_dm(self) -> bool:
        """Check if this is a DM channel."""
        return self.type == 1


# ============================================
# DISCORD EMBED
# ============================================

class DiscordEmbedField(BaseModel):
    """Field in a Discord embed."""
    name: str = Field(..., description="Field name")
    value: str = Field(..., description="Field value")
    inline: Optional[bool] = Field(False, description="Whether field is inline")


class DiscordEmbedAuthor(BaseModel):
    """Author in a Discord embed."""
    name: str = Field(..., description="Author name")
    url: Optional[str] = Field(None, description="Author URL")
    icon_url: Optional[str] = Field(None, description="Author icon URL")


class DiscordEmbedFooter(BaseModel):
    """Footer in a Discord embed."""
    text: str = Field(..., description="Footer text")
    icon_url: Optional[str] = Field(None, description="Footer icon URL")


class DiscordEmbed(BaseModel):
    """
    Discord embed (rich message format).
    
    Embeds allow rich formatting with colors, images, fields, etc.
    """
    title: Optional[str] = Field(None, description="Embed title")
    description: Optional[str] = Field(None, description="Embed description")
    url: Optional[str] = Field(None, description="URL of title")
    color: Optional[int] = Field(None, description="Color (decimal)")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp")
    
    footer: Optional[DiscordEmbedFooter] = Field(None, description="Footer")
    author: Optional[DiscordEmbedAuthor] = Field(None, description="Author")
    fields: Optional[List[DiscordEmbedField]] = Field(None, description="Fields")
    
    thumbnail: Optional[Dict[str, str]] = Field(None, description="Thumbnail image")
    image: Optional[Dict[str, str]] = Field(None, description="Main image")


# ============================================
# DISCORD MESSAGE
# ============================================

class DiscordAttachment(BaseModel):
    """Discord message attachment (file)."""
    id: str = Field(..., description="Attachment ID")
    filename: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    url: str = Field(..., description="URL to file")
    proxy_url: str = Field(..., description="Proxied URL")
    content_type: Optional[str] = Field(None, description="MIME type")
    width: Optional[int] = Field(None, description="Width (if image)")
    height: Optional[int] = Field(None, description="Height (if image)")


class DiscordMessage(BaseModel):
    """
    Discord message model.
    
    Represents a message in Discord (text, embed, file, etc.).
    """
    id: str = Field(..., description="Message ID (snowflake)")
    channel_id: str = Field(..., description="Channel ID where sent")
    guild_id: Optional[str] = Field(None, description="Guild ID (if in server)")
    
    # Author
    author: DiscordUser = Field(..., description="Message author")
    
    # Content
    content: str = Field(default="", description="Message text content")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    edited_timestamp: Optional[str] = Field(None, description="Last edit timestamp")
    
    # Rich content
    embeds: Optional[List[DiscordEmbed]] = Field(default_factory=list, description="Embeds")
    attachments: Optional[List[DiscordAttachment]] = Field(
        default_factory=list, 
        description="File attachments"
    )
    
    # Mentions
    mentions: Optional[List[DiscordUser]] = Field(
        default_factory=list,
        description="Users mentioned"
    )
    mention_everyone: Optional[bool] = Field(False, description="@everyone mentioned")
    
    # Reply info
    referenced_message: Optional['DiscordMessage'] = Field(
        None, 
        description="Message being replied to"
    )
    
    # Reactions
    reactions: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Reactions on message"
    )
    
    # Message type
    type: int = Field(default=0, description="Message type (0=default, 19=reply, etc.)")
    
    def is_reply(self) -> bool:
        """Check if this is a reply."""
        return self.referenced_message is not None or self.type == 19
    
    def has_embeds(self) -> bool:
        """Check if message has embeds."""
        return bool(self.embeds and len(self.embeds) > 0)
    
    def has_attachments(self) -> bool:
        """Check if message has file attachments."""
        return bool(self.attachments and len(self.attachments) > 0)
    
    def get_content(self) -> str:
        """Get message content (text or embed description)."""
        if self.content:
            return self.content
        
        if self.has_embeds() and self.embeds[0].description:
            return self.embeds[0].description
        
        return ""


# ============================================
# DISCORD INTERACTION
# ============================================

class DiscordInteraction(BaseModel):
    """
    Discord interaction (button click, slash command, etc.).
    """
    id: str = Field(..., description="Interaction ID")
    type: int = Field(..., description="Interaction type (2=slash, 3=component)")
    token: str = Field(..., description="Interaction token")
    
    user: Optional[DiscordUser] = Field(None, description="User who triggered")
    channel_id: str = Field(..., description="Channel ID")
    guild_id: Optional[str] = Field(None, description="Guild ID")
    
    data: Optional[Dict[str, Any]] = Field(None, description="Interaction data")


# Allow forward references
DiscordMessage.model_rebuild()
