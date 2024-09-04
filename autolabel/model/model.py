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

from autolabel.model.sam2 import SAM2


from typing import Dict, Any

class ModelFactory:

    _model_classes = {
        "sam2": "SAM2",
    }

    @classmethod
    def create(cls, model_name: str, **kwargs) -> Any:
        try:
            model_class = getattr(__import__(cls.__module__), cls._model_classes[model_name])
            return model_class(**kwargs)
        except KeyError:
            raise ValueError(f"Unknown model: {model_name}")
