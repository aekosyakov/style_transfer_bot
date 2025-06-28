#!/usr/bin/env python3
"""Main entry point for the Style Transfer Bot."""

import sys
import os
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the bot
from bot import main

if __name__ == "__main__":
    main() 