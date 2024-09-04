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
import sys
import logging

from autolabel.source.source import SourceFactory
from autolabel.model.model import ModelFactory
from autolabel.prompt.prompt import Prompt


def autolabel_image(model, source, prompt):
    model.predict(source.data, prompt)


def autolabel_video(model, source, prompt):
    model.predict(source.data, prompt)


def dispatch_task(model, source, prompt):
    TASKS = {
        ("SAM2", "ImageFileSource"): autolabel_image,
        ("SAM2", "VideoSource"): autolabel_video,
    }

    task = TASKS.get((type(model).__name__, type(source).__name__))

    if task is None:
        raise ValueError(
            f"No task found for model: {type(model).__name__}, source: {type(source).__name__}")

    task(model, source, prompt)


def autolabel(model_input, source_input, prompt_input):
    model = ModelFactory.create(model_input)
    source = SourceFactory.create(source_input)
    prompt = Prompt(prompt_input)

    dispatch_task(model, source, prompt)


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

    args = parser.parse_args(args[1:])

    # auto label
    autolabel(args.model, args.source, args.prompt)
