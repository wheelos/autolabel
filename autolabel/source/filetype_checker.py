#!/usr/bin/env python

# Copyright 2024 wheelos <daohu527@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import imghdr
import re
import mimetypes

from pathlib import Path
from urllib.parse import urlparse


def is_file(src: str) -> bool:
    """
    Check if the given path is a file.
    """
    return Path(src).is_file()


def is_path(src: str) -> bool:
    """
    Check if the given path is a valid path.
    """
    return Path(src).exists()


def is_url(src: str) -> bool:
    """
    Check if the source string is a valid URL.
    """
    try:
        result = urlparse(src)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_stream(src: str) -> bool:
    """
    Check if the given path represents video stream.
    """
    pattern = re.compile(
        r'^(rtsp://|rtmp://)[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    match = re.match(pattern, src)

    return bool(match)


def is_screenshot(src: str) -> bool:
    """
    Check if the given path is a screenshot.
    """
    pattern = r"^screen:\d+$"
    match = re.match(pattern, src)

    return bool(match)


def is_glob_pattern(src: str) -> bool:
    """
    Check if the given path contains glob-style wildcards.
    """
    pattern = r'^glob\(([^)]+)\)$'
    match = re.match(pattern, src)

    return bool(match)


def is_video(src: str) -> bool:
    """
    Check if the given path is a video file.
    """
    video_mime_types = {
        "video/x-msvideo",  # for avi files
        "video/mp4",        # for mp4 files
        "video/x-matroska",  # for mkv files
        "video/quicktime",  # for mov files
        "video/webm",       # for webm files
        "video/x-flv",      # for flv files
        "video/mpeg",       # for mpeg files
    }

    file_path = Path(src)
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type in video_mime_types


def is_image(src: str) -> bool:
    """
    Check if the given path is an image file.
    """
    return imghdr.what(src) is not None


def is_pcd(src: str) -> bool:
    """
    Check if the given path is a PCD file.
    """
    return Path(src).suffix.lower() == '.pcd'


def is_csv(src: str) -> bool:
    """
    Check if the given path is a CSV file.
    """
    return Path(src).suffix.lower() == '.csv'
