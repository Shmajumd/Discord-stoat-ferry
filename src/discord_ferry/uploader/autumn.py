"""Autumn file upload with retry."""

from pathlib import Path


async def upload_to_autumn(
    autumn_url: str,
    tag: str,
    file_path: Path,
    token: str,
) -> str:
    """Upload a file to Autumn and return the file ID.

    Args:
        autumn_url: Autumn server URL.
        tag: Upload tag (attachments, avatars, icons, banners, emojis).
        file_path: Local path to the file.
        token: Stoat session token.

    Returns:
        Autumn file ID string.
    """
    # TODO: implement
    raise NotImplementedError
