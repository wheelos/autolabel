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
import os
import requests
import sys

from pathlib import Path


# Download tmp path
DOWNLOAD_TMP_DIR = "/tmp/"
UNZIP_TMP_DIR = "/tmp/autolabel/"


def _progress(prefix, cur, total):
    bar_size = 50
    cur_p = int(cur / total * bar_size)
    print("{}[{}{}] {}/{}".format(prefix, "#"*cur_p, "."*(bar_size - cur_p),
                                  cur, total), end='\r', file=sys.stdout, flush=True)


def download_from_url(url: str) -> str:
    """Download file from url

    Args:
        url (str): url to download

    Returns:
        file: download file's path
    """
    local_filename = url.split('/')[-1]
    download_file = os.path.join(DOWNLOAD_TMP_DIR, local_filename)

    # File is cached
    if Path(download_file).is_file():
        logging.warning(
            "File downloaded before! use cached file in {}".format(download_file))
        return download_file

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        chunk_size = 8192
        total_length = int(r.headers.get('content-length', 0)) // chunk_size
        with open(download_file, 'wb') as f:
            for index, chunk in enumerate(r.iter_content(chunk_size)):
                f.write(chunk)
                _progress("Downloading:", index, total_length)
        print()
    return download_file


def url_process(src):
    file_path = None
    try:
        file_path = download_from_url(src)
    except Exception as e:
        logging.error("Download {} failed! {}".format(src, e))
    return file_path
