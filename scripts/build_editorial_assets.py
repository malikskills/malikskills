#!/usr/bin/env python3
"""Rebuild all static branding and project illustrations."""
try:
    from .artwork import build_editorial_assets
except ImportError:  # Script invocation: python3 scripts/build_editorial_assets.py
    from artwork import build_editorial_assets


if __name__ == "__main__":
    build_editorial_assets()
    print("Built MALIK DEV editorial SVG assets")
