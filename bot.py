#!/usr/bin/env python3
# coding: utf-8

"""
Proxy script to run epicbot package.
"""

import importlib
import os.path
import sys


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    importlib.import_module("epicbot.__main__").main()
