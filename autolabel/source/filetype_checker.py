"""
This Python script contains functions to check various types of files and paths.

Usage:
You can import these functions into your script and use them to check different types of files and paths. Additionally, you can add test code within the if __name__ == "__main__" block to validate the functionality of these functions.
"""

import os
import imghdr
import fnmatch
import mimetypes

def is_file(src: str) -> bool:
    """
    Check if the given path is a file.
    """
    return os.path.isfile(src)

def is_stream(src: str) -> bool:
    """
    Check if the given path represents a stream.
    """
    try:
        with open(src, 'rb') as file:
            return hasattr(file, 'readable') and hasattr(file, 'seekable')
    except IOError:
        return False

def is_screenshot(src: str) -> bool:
    """
    Check if the given path is a screenshot.
    """
    if not os.path.isfile(src) or not imghdr.what(src):
        return False

    # Check if the image dimensions are within typical screenshot resolutions
    typical_screenshot_resolutions = [(1920, 1080), (2560, 1440), (3840, 2160)]  # Add more if needed

    with open(src, 'rb') as f:
        img_bytes = f.read(24)  # Read the first 24 bytes of the image file

    width = img_bytes[16] + (img_bytes[17] << 8)
    height = img_bytes[20] + (img_bytes[21] << 8)

    for resolution in typical_screenshot_resolutions:
        if (width, height) == resolution:
            return True
    return False

def is_glob(src: str) -> bool:
    """
    Check if the given path contains glob-style wildcards.
    """
    return any(char in src for char in ('*', '?', '[')) or bool(fnmatch.translate(src))

def is_video(src: str) -> bool:
    """
    Check if the given path is a video file.
    """
    video_mime_types = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/x-flv"]

    mime_type, _ = mimetypes.guess_type(src)
    if mime_type in video_mime_types:
        return True

    return False

def is_image(src: str) -> bool:
    """
    Check if the given path is an image file.
    """
    return imghdr.what(src) is not None

def is_pcd(src: str) -> bool:
    """
    Check if the given path is a PCD file.
    """
    if src.endswith('.pcd'):
        return True
    else:
        return False
    
def is_csv(src: str) -> bool:
    """
    Check if the given path is a CSV file.
    """
    return src.lower().endswith('.csv')

def is_path(src: str) -> bool:
    """
    Check if the given path is a valid path.
    """
    return os.path.exists(src)

