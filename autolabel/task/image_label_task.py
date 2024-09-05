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

import torch
from autolabel.task.task import Task

from sam2.sam2_image_predictor import SAM2ImagePredictor


class ImageLabelTask(Task):
    def __init__(self, model) -> None:
        super().__init__()
        self._predictor = SAM2ImagePredictor(model)

    def set_data(self, data):
        self._data = data

    def add_prompt(self, prompt):
        self._prompts.append(prompt)

    def del_prompt(self, prompt):
        if prompt in self._prompts:
            self._prompts.remove(prompt)
        else:
            print(f"Prompt '{prompt}' does not exist!")

    def _combine_prompts(self):
        point_coords, point_labels = [], []

        for prompt in self._prompts:
            point_coords += prompt.point_coords
            point_labels += prompt.point_labels

        box = self._prompts[0].box
        mask_input = self._prompts[0].mask_input

        return point_coords, point_labels, box, mask_input

    def process(self):
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            self._predictor.set_image(self._data)
            point_coords, point_labels, box, mask_input = self._combine_prompts()
            masks, scores, logits = self._predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                box=box,
                mask_input=mask_input,
                multimask_output=False)
        return masks
