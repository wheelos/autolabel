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

class IterSource(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __iter__(self):
        pass

    @abc.abstractmethod
    def __next__(self):
        pass

class DirSource(IterSource):
    def __init__(self, source_input):
        self.source_input = source_input

    def __iter__(self):
        pass

    def __next__(self):
        pass

class CSVSource(self, source_input):
    def __init__(self, source_input)
        self.source_input = source_input

    def read_csv(self):
        pass

    def __iter__(self):
        pass

    def __next__(self):
        pass

class GlobSource(self, source_input):
    def __init__(self, source_input)
        self.source_input = source_input

    def collect_files(self):
      pass

    def __iter__(self):
        pass

    def __next__(self):
        pass
