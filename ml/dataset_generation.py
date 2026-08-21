import os
import sys
import csv

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_ROOT)

from benchmark.benchmark import benchmark_file
from ml.decision import (
    select_best_algorithm,
    save_ml_dataset_row
)
from monitoring.file_info import get_file_info

DATA_FOLDER = os.path.join(
    PROJECT_ROOT,
    "data"
)

DATASET_FILE = os.path.join(
    PROJECT_ROOT,
    "ml",
    "training_dataset.csv"
)

processed_files = set()

if os.path.exists(DATASET_FILE):
    with open(
        DATASET_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            if "File Name" in row and row["File Name"]:
                processed_files.add(row["File Name"])

print(f"Already processed: {len(processed_files)} files")

for filename in os.listdir(DATA_FOLDER):

    if filename.endswith(".enc"):
        continue

    if filename in processed_files:
        print(f"\nSkipping {filename} - already processed.")
        continue

    file_path = os.path.join(
        DATA_FOLDER,
        filename
    )

    if not os.path.isfile(file_path):
        continue

    print("\n================================")
    print(f"Processing: {filename}")
    print("================================")

    file_info = get_file_info(file_path)

    data_type = file_info["data_type"]
    file_size = file_info["size_bytes"]

    print(f"Data Type: {data_type}")
    print(f"File Size: {file_size} bytes")

    (
        benchmark_results,
        battery_ambient,
        cpu_ambient
    ) = benchmark_file(file_path)

    (
        best_algorithm,
        scores,
        security_weight,
        throughput_weight,
        cpu_weight
    ) = select_best_algorithm(
        benchmark_results,
        battery_ambient,
        file_size
    )

    print("\n--- Decision ---")

    print(f"Battery Ambient: {battery_ambient}%")
    print(f"CPU Ambient: {cpu_ambient}%")
    print(f"Security Weight: {security_weight:.2f}")
    print(f"Throughput Weight: {throughput_weight:.2f}")
    print(f"CPU Weight: {cpu_weight:.2f}")

    print("\n--- Scores ---")

    for algorithm, score in scores.items():
        print(f"{algorithm}: {score:.4f}")

    print(f"\nBest Algorithm: {best_algorithm}")

    save_ml_dataset_row(
        filename,
        data_type,
        file_size,
        cpu_ambient,
        battery_ambient,
        best_algorithm
    )

    print("Dataset row saved.")

    processed_files.add(filename)