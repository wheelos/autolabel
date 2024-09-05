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
from sam2.build_sam import build_sam2


class ModelFactory:
    def __init__(self) -> None:
        self.device = self._get_device()
        self._configure_device()

    def _get_device(self):
        # select the device for computation
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    def _configure_device(self):
        # configure the device settings based on type
        if self.device.type == "cuda":
            # use bfloat16 for the entire session
            torch.autocast("cuda", dtype=torch.bfloat16).__enter__()
            # enable tfloat32 for Ampere GPUs
            if torch.cuda.get_device_properties(0).major >= 8:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
        elif self.device.type == "mps":
            print("\nSupport for MPS devices is preliminary. SAM 2 is trained with CUDA and might "
                  "give numerically different outputs and sometimes degraded performance on MPS. "
                  "See e.g. https://github.com/pytorch/pytorch/issues/84936 for a discussion.")
        print(f"Using device: {self.device}")

    @staticmethod
    def create(self, model: str, model_cfg: str):
        if 'sam2' in model.lower():
            return build_sam2(model_cfg, model, device=self.device)
        else:
            raise ValueError(f"Model '{model}' is not supported.")
