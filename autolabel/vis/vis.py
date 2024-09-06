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

import cv2
import numpy as np


np.random.seed(3)


def show_mask(image, mask, random_color=False, borders=True):
    # Generate color
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])

    mask = mask.astype(np.uint8)
    h, w = mask.shape[-2:]
    mask_image = np.zeros((h, w, 3), dtype=np.uint8)

    # Map the mask to color
    mask_idx = mask > 0
    mask_image[mask_idx] = (color[:3] * 255).astype(np.uint8)

    # Draw contours if borders are enabled
    if borders:
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask_image = cv2.drawContours(
            mask_image, contours, -1, (255, 255, 255), thickness=2)

    # Overlay the mask onto the image
    overlay_image = cv2.addWeighted(image, 1, mask_image, color[3], 0)
    return overlay_image


def show_points(image, coords, labels, marker_size=10):
    # Draw positive and negative points
    pos_points = coords[labels == 1]
    neg_points = coords[labels == 0]

    for point in pos_points:
        cv2.drawMarker(image, tuple(point), color=(0, 255, 0), markerType=cv2.MARKER_STAR,
                       markerSize=marker_size, thickness=2, line_type=cv2.LINE_AA)

    for point in neg_points:
        cv2.drawMarker(image, tuple(point), color=(0, 0, 255), markerType=cv2.MARKER_STAR,
                       markerSize=marker_size, thickness=2, line_type=cv2.LINE_AA)

    return image


def show_box(image, box):
    x0, y0, x1, y1 = box
    cv2.rectangle(image, (int(x0), int(y0)), (int(x1), int(y1)),
                  color=(0, 255, 0), thickness=2)
    return image


def show_masks(image, masks, scores, point_coords=None, box_coords=None, input_labels=None, borders=True):
    for i, (mask, score) in enumerate(zip(masks, scores)):
        # Display mask
        overlay_image = show_mask(image.copy(), mask, borders=borders)

        # Display points
        if point_coords is not None and input_labels is not None:
            overlay_image = show_points(
                overlay_image, point_coords, input_labels)

        # Display bounding box
        if box_coords is not None:
            overlay_image = show_box(overlay_image, box_coords)

        # Add score text
        if len(scores) > 1:
            cv2.putText(overlay_image, f"Mask {i+1}, Score: {score:.3f}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Display image
        cv2.imshow(f"Mask {i+1}", overlay_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
