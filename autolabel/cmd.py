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

from source.source import SourceFactory
from model.model import ModelFactory
from prompt.prompt import Prompt



def autolabel_image(model, source, prompt):
    model.predict(source.data, prompt)

def autolabel_video(model, source, prompt):
    model.predict(source.data, prompt)

def _task_key(key1, key2):
    return (type(key1).__name__, type(key2).__name__)

def dispatch_task(model, source, prompt):
    TASKS = {
        ("SAM2", "ImageFileSource") : autolabel_image,
        ("SAM2", "VideoSource") : autolabel_video,
    }

    task_name = _task_key(model, source)
    task = TASKS[task_name]
    task(model, source, prompt)

def autolabel(source_input, prompt_input, model_input):
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
    autolabel(args.source, args.prompt, args.model)
