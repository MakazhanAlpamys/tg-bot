"""
Utility functions for the Telegram analytics bot.
"""
import logging
from typing import List


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )


def chunk_text(text: str, max_length: int = 4096) -> List[str]:
    """
    Split text into chunks that fit within Telegram's message length limit.
    Telegram has a 4096 character limit per message.
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by lines to avoid breaking mid-sentence
    lines = text.split('\n')
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If a single line is too long, split it
            if len(line) > max_length:
                for i in range(0, len(line), max_length):
                    chunks.append(line[i:i + max_length])
                current_chunk = ""
            else:
                current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def format_username(user) -> str:
    """Extract and format username from Telegram user object."""
    if user.username:
        return f"@{user.username}"
    elif user.first_name:
        full_name = user.first_name
        if user.last_name:
            full_name += f" {user.last_name}"
        return full_name
    else:
        return f"User{user.id}"
