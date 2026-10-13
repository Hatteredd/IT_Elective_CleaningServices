"""CleanHome PH — Desktop Application Entry Point (Tkinter).

Run:
    python run.py
"""
import sys
import os

# Ensure the project root is on sys.path so app and gui import correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import run

if __name__ == '__main__':
    run()
