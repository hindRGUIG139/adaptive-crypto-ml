import os
import sys
from benchmark.benchmark import benchmark_file

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DATA_FOLDER = "data"
for filename in os.listdir(DATA_FOLDER):
    file_path = os.path.join(DATA_FOLDER, filename)
    if filename.endswith(".enc"):
        continue
    file_path = os.path.join(DATA_FOLDER, filename)

    if os.path.isfile(file_path):
        benchmark_file(file_path)