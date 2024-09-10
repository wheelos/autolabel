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


import argparse
from enum import Enum
import sys
import yaml
import numpy as np

from autolabel.source.source_factory import SourceFactory
from autolabel.model.model_factory import ModelFactory
from autolabel.prompt.prompt import Prompt
from autolabel.task.image_segment_task import ImageSegmentTask
from autolabel.task.image_detection_task import ImageDetectionTask
from autolabel.task.video_segment_tracking_task import VideoSegmentTrackingTask


class TaskType(Enum):
    IMAGE_SEGMENT = "image_segment"
    IMAGE_DETECTION = "image_detection"
    VIDEO_SEGMENT = "video_segment"


def dispatch_task(task_type, model, source, prompt):
    if TaskType(task_type) == TaskType.IMAGE_SEGMENT:
        task = ImageSegmentTask(model)
        # Todo(zero): Determine whether the source can be iterated.
        # If it is an iterable type, traverse it. If not, get the data directly.
        task.set_data(source.data)
        task.add_prompt(prompt)
        masks = task.process()
    elif TaskType(task_type) == TaskType.IMAGE_DETECTION:
        task = ImageDetectionTask(model)
        task.set_data(source.data)
        results = task.process()
    elif TaskType(task_type) == TaskType.VIDEO_SEGMENT:
        task = VideoSegmentTrackingTask(model)

        # todo(zero): The design of the slice interface and the data type of the feedback,
        # can the data in the memory be directly passed to the model to avoid loading twice?
        # However, it is necessary to save the intercepted pictures.
        # The video source adds the property of whether to save the captured image.
        # Where is the path of the pictures? Where to set
        source.slice(2, True)
        task.set_data('/tmp/autolabel/')
        task.add_prompt(prompt)
        results = task.process()
    else:
        raise NotImplementedError(f'{task_type}')


def autolabel(config_file):
    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)

    # task_type
    task_type = data['task_type']

    # model
    model = data['model']['checkpoint']
    model_cfg = data['model'].get('model_cfg', None)
    # todo(zero): According to the different tasks of the model,
    # a new parameter task_type is added, but the interface can be optimized
    model = ModelFactory.create(model, model_cfg, task_type)

    # source
    source = SourceFactory.create(data.get('source'))

    # prompt
    prompt_data = data.get('prompt', {})
    prompt = Prompt(
        prompt_data.get('point_coords', None),
        prompt_data.get('point_labels', None),
        prompt_data.get('box', None),
        prompt_data.get('mask_input', None)
    )

    dispatch_task(task_type, model, source, prompt)


def main(args=sys.argv):
    """_summary_

    Args:
        args (_type_, optional): _description_. Defaults to sys.argv.
    """
    parser = argparse.ArgumentParser(
        description="autolabel is a auto label data tool.",
        prog="cmd.py")

    parser.add_argument(
        "-s", "--source", action="store", type=str, required=False,
        nargs='?', const="", help="source")
    parser.add_argument(
        "-p", "--prompt", action="store", type=str, required=False,
        nargs='?', const="", help="prompt")
    parser.add_argument(
        "-m", "--model", action="store", type=str, required=False,
        nargs='?', const="", help="model")
    parser.add_argument(
        "-c", "--config", action="store", type=str, required=False,
        nargs='?', const="", help="config")

    args = parser.parse_args(args[1:])

    # auto label
    if args.config:
        autolabel(args.config)
