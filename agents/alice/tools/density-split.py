#!/usr/bin/env python3
"""Compatibility shim: this tool is now tools/map-axis-split.py --axis density.

Kept so the invocations recorded in TRAINING_LOG.md before iteration 44 still
run. New work should call map-axis-split.py directly and say which axis it cut.
"""
import os, sys
os.execv(sys.executable,
         [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "map-axis-split.py"), "--axis", "density"] + sys.argv[1:])
