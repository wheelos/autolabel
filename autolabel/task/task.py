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


class Task(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._data = None
        self._prompt = None

    @abc.abstractmethod
    def set_data(self, data):
        pass

    @abc.abstractmethod
    def add_prompt(self, prompt):
        pass

    @abc.abstractmethod
    def del_prompt(self, prompt):
        pass

    @abc.abstractmethod
    def process(self):
        # return label results
        pass
