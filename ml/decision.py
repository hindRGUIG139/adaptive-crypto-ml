from benchmark.benchmark import benchmark_file
from monitoring.file_info import get_file_info
import csv


SECURITY_SCORES = {
    "AES": 3,
    "ChaCha20": 3,
    "PRESENT": 1,
}

SECURITY_WEIGHT = 0.30

PRESENT_MAX_BYTES = 16 * 1024 * 1024


def apply_security_gate(benchmark_results, file_size):

    if file_size > PRESENT_MAX_BYTES:
        return {
            algorithm: data
            for algorithm, data in benchmark_results.items()
            if algorithm != "PRESENT"
        }

    return benchmark_results


def normalize_higher_is_better(values):

    minimum = min(values.values())
    maximum = max(values.values())

    if maximum == minimum:
        return {
            algorithm: 1.0
            for algorithm in values
        }

    return {
        algorithm: (value - minimum) / (maximum - minimum)
        for algorithm, value in values.items()
    }


def normalize_lower_is_better(values):

    minimum = min(values.values())
    maximum = max(values.values())

    if maximum == minimum:
        return {
            algorithm: 1.0
            for algorithm in values
        }

    return {
        algorithm: (maximum - value) / (maximum - minimum)
        for algorithm, value in values.items()
    }


def calculate_scores(
    benchmark_results,
    battery_level,
    file_size
):

    candidates = apply_security_gate(
        benchmark_results,
        file_size
    )

    throughputs = {
        algorithm: data["throughput"]
        for algorithm, data in candidates.items()
    }

    cpu_cost = {
        algorithm: data["cpu"] * data["encryption_time"]
        for algorithm, data in candidates.items()
    }

    throughput_scores = normalize_higher_is_better(
        throughputs
    )

    cpu_scores = normalize_lower_is_better(
        cpu_cost
    )

    security_scores = {
        algorithm: SECURITY_SCORES[algorithm] / 3
        for algorithm in candidates
    }

    remaining_budget = 1.0 - SECURITY_WEIGHT

    battery_ratio = battery_level / 100

    throughput_ratio = (
        0.30 + (0.40 * battery_ratio)
    )

    cpu_ratio = 1 - throughput_ratio

    throughput_weight = (
        remaining_budget * throughput_ratio
    )

    cpu_weight = (
        remaining_budget * cpu_ratio
    )

    scores = {}

    for algorithm in candidates:

        scores[algorithm] = (
            SECURITY_WEIGHT
            * security_scores[algorithm]

            + throughput_weight
            * throughput_scores[algorithm]

            + cpu_weight
            * cpu_scores[algorithm]
        )

    return (
        scores,
        SECURITY_WEIGHT,
        throughput_weight,
        cpu_weight
    )


def select_best_algorithm(
    benchmark_results,
    battery_level,
    file_size
):

    (
        scores,
        security_weight,
        throughput_weight,
        cpu_weight
    ) = calculate_scores(
        benchmark_results,
        battery_level,
        file_size
    )

    best_algorithm = max(
        scores,
        key=lambda algorithm: (
            scores[algorithm],
            SECURITY_SCORES[algorithm]
        )
    )

    return (
        best_algorithm,
        scores,
        security_weight,
        throughput_weight,
        cpu_weight
    )


def save_ml_dataset_row(
    filename,
    data_type,
    file_size,
    cpu_ambient,
    battery_ambient,
    best_algorithm
):

    with open(
        "ml/training_dataset.csv",
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        if file.tell() == 0:
            writer.writerow([
                "File Name",
                "Data Type",
                "File Size (Bytes)",
                "CPU Ambient (%)",
                "Battery Ambient (%)",
                "Best Algorithm"
            ])

        writer.writerow([
            filename,
            data_type,
            file_size,
            cpu_ambient,
            battery_ambient,
            best_algorithm
        ])

def main():

    path = "data/sample_100KB.txt"
    file_info = get_file_info(path)
    data_type = file_info["data_type"]
    file_size = file_info["size_bytes"]

    (
        benchmark_results,
        battery_ambient,
        cpu_ambient
    ) = benchmark_file(path)

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

    print(
        f"\nBattery Level Ambient: "
        f"{battery_ambient}%"
    )

    print(
        f"CPU Level Ambient: "
        f"{cpu_ambient}%"
    )

    print(
        f"File Size: "
        f"{file_size} bytes"
    )

    print(
        f"Security Weight: "
        f"{security_weight:.2f}"
    )

    print(
        f"Throughput Weight: "
        f"{throughput_weight:.2f}"
    )

    print(
        f"CPU Weight: "
        f"{cpu_weight:.2f}"
    )

    print("\n--- Scores ---")

    for algorithm, score in scores.items():

        print(
            f"{algorithm}: "
            f"{score:.4f}"
        )

    print(
        f"\nBest Algorithm: "
        f"{best_algorithm}"
    )

    save_ml_dataset_row(
        data_type,
        file_size,
        cpu_ambient,
        battery_ambient,
        best_algorithm
    )

if __name__ == "__main__":
    main()