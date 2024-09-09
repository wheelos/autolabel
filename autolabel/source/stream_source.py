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


import abc
import time
import cv2
from PIL import Image
from typing import Iterator, List


class StreamSource(metaclass=abc.ABCMeta):
    def __init__(self, source_input: str, interval: int):
        if interval <= 0:
            raise ValueError("Interval must be positive")
        self._interval = interval
        self.source_input = source_input

    @abc.abstractmethod
    def __iter__(self) -> Iterator['StreamSource']:
        pass

    @abc.abstractmethod
    def capture(self) -> Image.Image:
        pass

    @abc.abstractmethod
    def slice(self, duration: float) -> List[Image.Image]:
        pass

    @property
    def interval(self) -> int:
        return self._interval

    @interval.setter
    def interval(self, value: int):
        if value <= 0:
            raise ValueError("Interval must be positive")
        self._interval = value


class ScreenshotSource(StreamSource):
    def __init__(self, interval: int):
        super().__init__(interval)

    def capture(self) -> Image.Image:
        frame = cv2.cvtColor(cv2.imread(0), cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)

    def slice(self, duration: float) -> List[Image.Image]:
        """Capture screenshots for a specified duration, with each screenshot taken at self.interval."""
        screenshots = []
        end_time = time.time() + duration
        while time.time() < end_time:
            screenshots.append(self.capture())
            time.sleep(self.interval)
        return screenshots

    def __iter__(self) -> Iterator[Image.Image]:
        while True:
            yield self.capture()
            time.sleep(self.interval)


class VideoSource(StreamSource):
    def __init__(self, source_input: str, interval: int):
        super().__init__(source_input, interval)
        video_path = self.source_input.input
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(
                f"Could not open video source: {video_path}")

    def capture(self) -> Image.Image:
        ret, frame = self.cap.read()
        if not ret:
            raise ValueError("End of video stream")
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def slice(self, duration: float, save_img: bool) -> List[Image.Image]:
        images = []
        start_time = self.cap.get(cv2.CAP_PROP_POS_MSEC)
        # Convert duration to milliseconds
        end_time = start_time + (duration * 1000)

        while self.cap.get(cv2.CAP_PROP_POS_MSEC) < end_time:
            try:
                img = self.capture()
                images.append(img)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                             self.cap.get(cv2.CAP_PROP_POS_FRAMES) + self.interval)

                if save_img:
                    cur_time = self.cap.get(cv2.CAP_PROP_POS_MSEC)
                    cv2.imwrite(f'/tmp/autolabel/{cur_time}.jpg', img)
            except StopIteration:
                break

        return images

    def __iter__(self):
        while True:
            yield self.capture()
            self.cap.set(cv2.CAP_PROP_POS_FRAMES,
                         self.cap.get(cv2.CAP_PROP_POS_FRAMES) + self.interval)

    def __del__(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()


class VideoStreamSource(StreamSource):
    def __init__(self, source_input: str, interval: int):
        super().__init__(source_input, interval)
        video_url = self.source_input.input
        self.cap = cv2.VideoCapture(video_url)
        if not self.cap.isOpened():
            raise ValueError(
                f"Could not open video source: {video_url}")

    def capture(self) -> Image.Image:
        ret, frame = self.cap.read()
        if not ret:
            raise ValueError("Read video stream failed!")
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def slice(self, duration: float) -> List[Image.Image]:
        images = []
        end_time = time.time() + duration
        while time.time() < end_time:
            try:
                images.append(self.capture())
                time.sleep(self.interval)
            except ValueError:
                break
        return images

    def __iter__(self):
        while True:
            yield self.capture()
            time.sleep(self.interval)

    def __del__(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()
