#!/usr/bin/env python3
import os

os.environ["FLAG_STORE"] = "2"
os.environ["PWNLIB_NOTERM"] = "1"

from service3_common import *
