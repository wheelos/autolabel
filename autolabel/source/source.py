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

from enum import Enum

from autolabel.source.filetype_checker import (
    is_url,
    is_file,
    is_image,
    is_video,
    is_pcd,
    is_csv,
    is_path,
    is_stream,
    is_screenshot,
    is_glob_pattern
)
from autolabel.source.file_source import ImageFileSource, PCDFileSource
from autolabel.source.iter_source import DirSource, CSVSource, GlobSource
from autolabel.source.stream_source import ScreenshotSource, VideoSource, VideoStreamSource
from autolabel.source.process import url_process


class SourceInputType(Enum):
    IMAGE_FILE = 1
    POINT_CLOUD_FILE = 2
    CSV_FILE = 3
    VIDEO_FILE = 4
    VIDEO_STREAM = 5
    SCREENSHOT = 6
    DIRECTORY = 7
    GLOB_PATTERN = 8


class SourceInput:
    def __init__(self, input_str: str) -> None:
        self.raw_input = input_str

        self._input = self._process_input(input_str)
        # Get source input type
        self.input_type = self._get_source_type()

    def _process_input(self, input_str):
        # If "raw_input" is a url, we first download it to the tmp directory
        # and then process it as a file
        if is_url(input_str):
            return url_process(input_str)
        else:
            return input_str

    def _get_source_type(self) -> None:
        if is_file(self._input):
            if is_image(self._input):
                return SourceInputType.IMAGE_FILE
            elif is_video(self._input):
                return SourceInputType.VIDEO_FILE
            elif is_pcd(self._input):
                return SourceInputType.POINT_CLOUD_FILE
            elif is_csv(self._input):
                return SourceInputType.CSV_FILE
        elif is_path(self._input):
            return SourceInputType.DIRECTORY
        elif is_stream(self._input):
            return SourceInputType.VIDEO_STREAM
        elif is_screenshot(self._input):
            return SourceInputType.SCREENSHOT
        elif is_glob_pattern(self._input):
            return SourceInputType.GLOB_PATTERN
        else:
            raise NotImplementedError(f'Not supported type: {self._input}')

    @property
    def input(self):
        return self._input

    @property
    def type(self):
        return self.input_type


class SourceFactory:
    @staticmethod
    def create(input_str: str):
        source_input = SourceInput(input_str)
        source_type = source_input.type

        if source_type == SourceInputType.IMAGE_FILE:
            return ImageFileSource(source_input)
        elif source_type == SourceInputType.POINT_CLOUD_FILE:
            return PCDFileSource(source_input)
        elif source_type == SourceInputType.DIRECTORY:
            return DirSource(source_input)
        elif source_type == SourceInputType.CSV_FILE:
            return CSVSource(source_input)
        elif source_type == SourceInputType.GLOB_PATTERN:
            return GlobSource(source_input)
        elif source_type == SourceInputType.SCREENSHOT:
            return ScreenshotSource(source_input)
        elif source_type == SourceInputType.VIDEO_STREAM:
            return VideoStreamSource(source_input)
        elif source_type == SourceInputType.VIDEO_FILE:
            return VideoSource(source_input)
        else:
            raise NotImplementedError(f'Not supported type: {source_type}')
