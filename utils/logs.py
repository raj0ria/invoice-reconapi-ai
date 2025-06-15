"""
Filename: logs.py
Author: Ashish Sharma
Date created: 15/06/2025
License: MIT License
Description: Logging utility functions.
"""

import logging

# Configure logging to print logs to console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the root logger
root_logger = logging.getLogger()

# Set the level of the root logger to DEBUG
root_logger.setLevel(logging.INFO)

# Define a logger
logger = logging.getLogger(__name__)