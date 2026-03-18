#!/usr/bin/env python3
# DEPRECATED — DO NOT USE DIRECTLY. Use build_musigma_report.py instead.
"""
assemble_report.py — Thin forwarding shim.
All report generation is handled by build_musigma_report.py (the single canonical
report generator). This file exists only for backward compatibility — any invocation
is forwarded to build_musigma_report.main().
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_musigma_report


def main():
    build_musigma_report.main()


if __name__ == "__main__":
    main()
