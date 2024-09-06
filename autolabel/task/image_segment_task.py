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

import logging
import torch
import numpy as np
from sam2.sam2_image_predictor import SAM2ImagePredictor

from autolabel.task.task import Task
from autolabel.vis.vis import show_masks


class ImageSegmentTask(Task):
    def __init__(self, model) -> None:
        super().__init__()
        self._predictor = SAM2ImagePredictor(model)

    def set_data(self, data):
        self._data = np.array(data.convert("RGB"))

    def add_prompt(self, prompt):
        self._prompts.append(prompt)

    def del_prompt(self, prompt):
        if prompt in self._prompts:
            self._prompts.remove(prompt)
        else:
            print(f"Prompt '{prompt}' does not exist!")

    def _combine_prompts(self):
        point_coords = []
        point_labels = []

        for prompt in self._prompts:
            if prompt.point_coords:
                point_coords.extend(prompt.point_coords)
            if prompt.point_labels:
                point_labels.extend(prompt.point_labels)

        point_coords = np.array(point_coords) if point_coords else None
        point_labels = np.array(point_labels) if point_labels else None

        first_prompt = self._prompts[0]
        box = np.array(first_prompt.box) if first_prompt.box else None
        mask_input = np.array(
            first_prompt.mask_input) if first_prompt.mask_input else None

        return point_coords, point_labels, box, mask_input

    def process(self):
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            self._predictor.set_image(self._data)
            point_coords, point_labels, box, mask_input = self._combine_prompts()
            print(f'point_coords: {point_coords}')
            print(f'point_labels: {point_labels}')
            print(f'box: {box}')
            print(f'mask_input: {mask_input}')
            masks, scores, logits = self._predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                box=box,
                mask_input=mask_input,
                multimask_output=False)

        show_masks(self._data, masks, scores, point_coords=point_coords,
                   input_labels=point_labels, box_coords=box, borders=True)
        return masks
