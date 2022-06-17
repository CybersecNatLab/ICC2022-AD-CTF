#!/usr/bin/env python3
import os

os.environ["FLAG_STORE"] = "1"
os.environ["PWNLIB_NOTERM"] = "1"

from service3_common import *
