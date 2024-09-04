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
from sam2.sam2_image_predictor import SAM2ImagePredictor, SAM2VideoPredictor


class SAM2:
    def __init__(self, task_type):
        if task_type == "video":
            self.predictor = SAM2VideoPredictor.from_pretrained(
                "facebook/sam2-hiera-large")
        elif task_type == "image":
            self.predictor = SAM2ImagePredictor.from_pretrained(
                "facebook/sam2-hiera-large")

    def predict_image(self, data, prompt):
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            self.predictor.set_image(data)
            masks, scores, logits = self.predictor.predict(
                point_coords=prompt.point_coords,
                point_labels=prompt.point_labels,
                box=prompt.box,
                mask_input=prompt.mask_input,
                multimask_output=False)
        return masks

    def predict_video(self, data, prompt):
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            state = self.predictor.init_state( < your_video > )

            # add new prompts and instantly get the output on the same frame
            frame_idx, object_ids, masks = self.predictor.add_new_points_or_box(
                state, points=prompt.point_coords, labels=prompt.point_labels, box=prompt.box)

            # propagate the prompts to get masklets throughout the video
            for frame_idx, object_ids, masks in self.predictor.propagate_in_video(state):
                pass
