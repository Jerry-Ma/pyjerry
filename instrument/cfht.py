#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2016-08-17 22:51
# Python Version :  2.7.12
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
cfht.py
"""


def get_bpm_file(image):
    pass


def get_bbox():
    w = 33. / 60.
    return (-w, w), (-w, w)


def get_chip_rect():
    return (0, 2112), (0, 4644)


def get_chip_layout():
    return 4, 9


def get_chip_num():
    return 36


def get_chip_xy(ext):
    ny, nx = get_chip_layout()
    y = (ext - 1) / nx + 1
    x = (ext - 1) % nx + 1
    return 10 * x + y
