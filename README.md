# autolabel

<!-- [![Documentation Status](https://readthedocs.org/projects/cyber-record/badge/?version=latest)](https://cyber-record.readthedocs.io/en/latest/?badge=latest)

**[autolabel](https://cyber-record.readthedocs.io/en/latest/)** is a cyber record file offline parse tool. You can use `autolabel` to read messages from record file, or write messages to the record file. -->

| os      | support                 | remark |
|---------|-------------------------|--------|
| ubuntu  | :heavy_check_mark:      |        |
| mac     | :heavy_check_mark:      |        |
| windows | :heavy_check_mark:      |        |


## Quick start
Install "autolabel" by the following command.
```sh
# install sam2
pip3 install 'git+https://github.com/facebookresearch/segment-anything-2.git'

# install autolabel
cd autolabel & pip3 install -e .
# pip3 install whl-autolabel
```

download pretrained model
```
cd autolabel/checkpoints/ & bash download_ckpts.sh
```

## Command
You can easily automatically label images using the following command.

```
autolabel -c=autolabel/conf.yaml
```

## Parameters

## Questiones

1. ImportError: libGL.so.1: cannot open shared object file: No such file or directory

```
pip install opencv-python-headless
```
