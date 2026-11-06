#!/usr/bin/env python3
"""
Convenience entry point for Mini-Courier Planner execution.
Runs the complete capstone demonstration and generates all figures and datasets.
"""
import sys
import os

# Ensure current workspace is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import run_pipeline_demo

if __name__ == "__main__":
    output = run_pipeline_demo(vehicle_capacity=40, output_dir="images")
    print(output)
