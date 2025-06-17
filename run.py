#!/usr/bin/env python3
"""
Main entry point for the disk monitoring webhook server.
"""

import sys
import os

# Change to webhook_server directory
os.chdir('webhook_server')

# Import and run the Flask app
exec(open('app.py').read())