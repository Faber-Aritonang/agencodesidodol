"""Pastikan root project ada di sys.path apapun cara pytest dipanggil."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
