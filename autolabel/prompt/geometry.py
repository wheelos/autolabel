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


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class AABBBox:
    """
    (x_min, y_min)
        +------------------------+
        |                        |
        |                        |
        |                        |
        |                        |
        +------------------------+
                        (x_max, y_max)
    """
    def __init__(self, xy_min, xy_max):
        self.xy_min = xy_min
        self.xy_max = xy_max

class Polygon:
    def __init__(self, points):
        self.points = points

