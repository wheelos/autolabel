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
from task.image_label_task import ImageLabelTask


class TaskType(Enum):
    IMAGE_LABEL = "image_label"
    VIDEO_LABEL = "video_label"


def dispatch_task(task_type, model, source, prompt):
    if TaskType(task_type) == TaskType.IMAGE_LABEL:
        task = ImageLabelTask(model)
        task.set_data(source)
        task.add_prompt(prompt)
        masks = task.process()


def autolabel(config_file):
    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)

    # task_type
    task_type = data['task_type']

    # model
    model = data['model']['checkpoint']
    model_cfg = data['model']['model_cfg']
    model = ModelFactory.create(model, model_cfg)

    # source
    source = SourceFactory.create(data['source'])

    # prompt
    prompt_data = data['prompt']
    prompt = Prompt(
        np.array(prompt_data['point_coords']),
        np.array(prompt_data['point_labels']),
        np.array(prompt_data['box']),
        np.array(prompt_data['mask_input'])
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
