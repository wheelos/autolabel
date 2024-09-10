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
import numpy as np

from autolabel.task.task import Task
from autolabel.vis.vis import show_mask1

import os
import cv2


class VideoSegmentTrackingTask(Task):
    def __init__(self, model) -> None:
        super().__init__()
        self._predictor = model

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

        return point_coords, point_labels, box

    def process(self):
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            inference_state = self._predictor.init_state(video_path=self._data)

            # todo(zero): Add new interactive methods to select points or
            # rectangles to specify the data to be labeled and visualize them
            point_coords, point_labels, box = self._combine_prompts()
            ann_frame_idx, ann_obj_id = 0, 0
            # add new prompts and instantly get the output on the same frame
            frame_idx, object_ids, masks = self._predictor.add_new_points_or_box(
                inference_state=inference_state,
                frame_idx=ann_frame_idx,
                obj_id=ann_obj_id,
                points=point_coords,
                labels=point_labels,
                box=box)

            # propagate the prompts to get masklets throughout the video
            video_segments = {}
            for out_frame_idx, out_obj_ids, out_mask_logits in self._predictor.propagate_in_video(inference_state):
                video_segments[out_frame_idx] = {
                    out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                    for i, out_obj_id in enumerate(out_obj_ids)
                }

            # todo(zero): Optimize visualization methods, especially the order of images
            # scan all the JPEG frame names in this directory.
            # Design a way to achieve a one-to-one correspondence between images
            # and annotation results. This may require modifying the arrangement of images in sam2.
            frame_names = [
                p
                for p in os.listdir(self._data)
                if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
            ]
            frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))
            num_frames = len(frame_names)

            for out_frame_idx in range(num_frames):
                image_bgr = cv2.imread(os.path.join(
                    self._data, frame_names[out_frame_idx]), cv2.IMREAD_UNCHANGED)
                for out_obj_id, out_mask in video_segments[out_frame_idx].items():
                    show_mask1(image_bgr, out_mask, obj_id=out_obj_id)

            return video_segments
