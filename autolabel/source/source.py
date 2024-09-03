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
    def __init__(self, input_str : str) -> None:
        self.raw_input = input_str
        # Get source input type
        self.check_type()

    def check_type(self) -> None:
        # If "raw_input" is a url, we first download it to the tmp directory
        # and then process it as a file
        if is_url(self.raw_input):
            raw_input = url_process(self.raw_input)
        else:
            raw_input = self.raw_input

        # Returns the source input type according to the "raw_input" string
        if is_file(raw_input):
            if is_image(raw_input):
                self.input_type = SourceInputType.IMAGE_FILE
            elif is_video(raw_input):
                self.input_type = SourceInputType.VIDEO_FILE
            elif is_pcd(raw_input):
                self.input_type = SourceInputType.POINT_CLOUD_FILE
            elif is_csv(raw_input):
                self.input_type = SourceInputType.CSV_FILE
        elif is_path(raw_input):
            self.input_type = SourceInputType.DIRECTORY
        elif is_stream(raw_input):
            self.input_type = SourceInputType.VIDEO_STREAM
        elif is_screenshot(raw_input):
            self.input_type = SourceInputType.SCREENSHOT
        elif is_glob_pattern(raw_input):
            self.input_type = SourceInputType.GLOB_PATTERN
        else:
            raise NotImplementedError(f'Not supported type: {raw_input}')

    @property
    def input(self):
        return self.raw_input

    @property
    def type(self):
        return self.input_type


class SourceFactory:
    @staticmethod
    def create(input_str : str):
        source_input = SourceInput(input_str)

        if source_input == SourceInputType.IMAGE_FILE:
            return ImageFileSource(source_input)
        elif source_input == SourceInputType.POINT_CLOUD_FILE:
            return PCDFileSource(source_input)
        elif source_input == SourceInputType.DIRECTORY:
            return DirSource(source_input)
        elif source_input == SourceInputType.CSV_FILE:
            return CSVSource(source_input)
        elif source_input == SourceInputType.GLOB_PATTERN:
            return GlobSource(source_input)
        elif source_input == SourceInputType.SCREENSHOT:
            return ScreenshotSource(source_input)
        elif source_input == SourceInputType.VIDEO_STREAM:
            return VideoStreamSource(source_input)
        elif source_input == SourceInputType.VIDEO_FILE:
            return VideoSource(source_input)
        else:
            raise NotImplementedError(f'Not supported type: {input_str}')
