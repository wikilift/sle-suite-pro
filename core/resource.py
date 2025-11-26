import sys
import os


def resource_path(relative_path: str) -> str:
 
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS  
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base, relative_path)
