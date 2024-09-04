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

import pytest

from autolabel.source.source import SourceInput, SourceInputType, SourceFactory

def test_url():
    url = "https://via.placeholder.com/300/09f/fff.png"
    src = SourceInput(url)
    assert src.input == "/tmp/fff.png"
    assert src.type == SourceInputType.IMAGE_FILE


def test_image_file_source():
    url = "https://via.placeholder.com/300/09f/fff.png"
    source = SourceFactory.create(url)
    assert source.data is not None
