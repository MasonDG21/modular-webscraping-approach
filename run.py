import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).resolve().parent / 'src'
sys.path.insert(0, str(src_path))

from src.main import main

if __name__ == "__main__":
    main()