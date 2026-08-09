from benchmark.benchmark import benchmark_file
def normalize_higher_is_better(values):
    """
    Higher value = better.
    Used for throughput.
    """
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
    """
    Lower value = better.
    Used for CPU usage.
    """

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


def calculate_scores(benchmark_results, battery_level):
    """
    Calculate a score for each algorithm.

    Battery level determines how important
    throughput and CPU usage are.
    """

    # Get the throughput of each algorithm.
    throughputs = {
        algorithm: data["throughput"]
        for algorithm, data in benchmark_results.items()
    }

    # Get the CPU usage of each algorithm.
    cpu_usage = {
        algorithm: data["cpu"]
        for algorithm, data in benchmark_results.items()
    }

    # Higher throughput = better.
    throughput_scores = normalize_higher_is_better(
        throughputs
    )

    # Lower CPU usage = better.
    cpu_scores = normalize_lower_is_better(
        cpu_usage
    )

    # Choose the weights according to battery level.
    if battery_level <= 20:
        throughput_weight = 0.30
        cpu_weight = 0.70

    elif battery_level <= 50:
        throughput_weight = 0.50
        cpu_weight = 0.50

    else:
        throughput_weight = 0.70
        cpu_weight = 0.30

    scores = {}

    for algorithm in benchmark_results:

        scores[algorithm] = (
            throughput_weight * throughput_scores[algorithm]
            + cpu_weight * cpu_scores[algorithm]
        )

    return scores, throughput_weight, cpu_weight

def select_best_algorithm(benchmark_results, battery_level):
    """
    Return the algorithm with the highest score.

    This becomes the 'Best Algorithm' label
    for the ML dataset.
    """

    scores, throughput_weight, cpu_weight = calculate_scores(
        benchmark_results,
        battery_level
    )

    best_algorithm = max(
        scores,
        key=scores.get
    )

    return (
        best_algorithm,
        scores,
        throughput_weight,
        cpu_weight
    )

def main():

    benchmark_results, battery_ambient = benchmark_file("data/sample_100KB.txt")
    (best_algorithm, scores, throughput_weight,cpu_weight) = select_best_algorithm(
    benchmark_results,battery_ambient)
    print(f"\nBattery Level ambient: {battery_ambient}%")
    print(f"Throughput Weight: {throughput_weight:.2f}")
    print(f"CPU Weight: {cpu_weight:.2f}")
    print("\n--- Best Algorithm ---")
    for algorithm, score in scores.items():
        print(f"{algorithm}: {score:.4f}")
    print(f"\nBest Algorithm: {best_algorithm}")

if __name__ == "__main__":
    main()