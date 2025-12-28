#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_input_dir() -> Path:
    if v := os.environ.get("OAK_TRADE_INPUT_DIR"):
        return Path(v)
    candidate = Path(__file__).resolve().parents[1] / "input"
    if candidate.exists():
        return candidate
    raise RuntimeError("Input data directory not found.")


@lru_cache
def get_output_dir() -> Path:
    if v := os.environ.get("OAK_TRADE_OUTPUT_DIR"):
        return Path(v)
    candidate = Path(__file__).resolve().parents[1] / "output"
    if candidate.exists():
        return candidate
    raise RuntimeError("Output data directory not found.")
