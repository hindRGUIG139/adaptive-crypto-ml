import os #interact with the operating system
import statistics
import time
from crypto_algorithms.aes import encrypt_file as aes_encrypt
from crypto_algorithms.present import encrypt_file as present_encrypt
from crypto_algorithms.chacha20 import encrypt_file as chacha20_encrypt
import sys
from monitoring.system_metrics import get_battery_level, get_cpu_usage
from monitoring.file_info import get_file_info
import csv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, PROJECT_ROOT)
def benchmark_algorithm(encrypt_function, input_file, output_file, key):
    times = []
    cpu_ambient= get_cpu_usage()
    battery_ambient = get_battery_level()
    for _ in range(10):
        start = time.perf_counter()
        encrypt_function(input_file, output_file, key)
        end = time.perf_counter()
        elapsed = end - start
        times.append(elapsed)
    cpu_after= get_cpu_usage()
    battery_after = get_battery_level()
    average_time = statistics.mean(times)
    standard_deviation = statistics.stdev(times)

    file_info = get_file_info(input_file)
    file_size = file_info["size_bytes"]
    file_size_mb = file_size / (1024 * 1024)
    throughput = file_size_mb / average_time
    
    return average_time, standard_deviation, cpu_ambient, battery_ambient, cpu_after, battery_after, throughput

def save_to_csv(data_type, file_size, algorithm, average_time, standard_deviation, throughput, cpu_ambient, battery_ambient, cpu_after, battery_after):
    with open("ml/dataset.csv", "a", newline="") as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(["Data Type","File Size (Bytes)", "Algorithm", "Average Time (s)", "Standard Deviation (s)",
                             "Throughput (MB/s)", "CPU Usage (%)","Battery Level (%)","CPU Usage After (%)","Battery Level After (%)"])
        writer.writerow([data_type, file_size, algorithm, average_time, standard_deviation, throughput, cpu_ambient, battery_ambient, cpu_after, battery_after])

def save_ml_row(data_type, file_size, cpu_ambient,
                battery_ambient, best_algorithm):

    with open("ml/training_dataset.csv", "a", newline="") as file:
        writer = csv.writer(file)

        # Write the header only when the file is empty.
        if file.tell() == 0:
            writer.writerow([
                "CPU Ambient (%)",
                "Battery Ambient (%)",
                "File Size (Bytes)",
                "Data Type",
                "Best Algorithm"
            ])

        writer.writerow([
            cpu_ambient,
            battery_ambient,
            file_size,
            data_type,
            best_algorithm
        ])

def benchmark_file(input_file):
    file_info = get_file_info(input_file)
    data_type = file_info["data_type"]
    file_size = file_info["size_bytes"]
    output_file = input_file + ".enc"
    
    key_aes = os.urandom(32)
    key_present = int.from_bytes(os.urandom(10), "big")
    key_chacha20 = os.urandom(32)

    print("Benchmarking AES...")
    aes_time, aes_std, aes_cpu_ambient, aes_battery_ambient, aes_cpu_after, aes_battery_after, aes_throughput = benchmark_algorithm(aes_encrypt, input_file, output_file, key_aes)
    
    print("Benchmarking PRESENT...")
    present_time, present_std ,present_cpu_ambient, present_battery_ambient, present_cpu_after, present_battery_after, present_throughput = benchmark_algorithm(present_encrypt, input_file, output_file, key_present)
    
    print("Benchmarking ChaCha20...")
    chacha20_time, chacha20_std ,chacha20_cpu_ambient, chacha20_battery_ambient, chacha20_cpu_after, chacha20_battery_after, chacha20_throughput= benchmark_algorithm(chacha20_encrypt, input_file, output_file, key_chacha20)
    #aes
    print(f"AES average encryption time: {aes_time:.6f} seconds")
    print(f"AES standard deviation: {aes_std:.6f} seconds")
    print(f"AES throughput: {aes_throughput:.2f} MB/s")
    print(f"CPU Usage: {aes_cpu_after}%")
    print(f"Battery Level: {aes_battery_after}%")
    save_to_csv(data_type, file_size, "AES", aes_time, aes_std, aes_throughput, aes_cpu_ambient, aes_battery_ambient, aes_cpu_after, aes_battery_after)
    #present
    print(f"PRESENT average encryption time: {present_time:.6f} seconds")
    print(f"PRESENT standard deviation: {present_std:.6f} seconds")
    print(f"PRESENT throughput: {present_throughput:.2f} MB/s")
    print(f"CPU Usage: {present_cpu_after}%")
    print(f"Battery Level: {present_battery_after}%")
    save_to_csv(data_type, file_size, "PRESENT", present_time, present_std, present_throughput, present_cpu_ambient, present_battery_ambient, present_cpu_after, present_battery_after)
    #chacha20
    print(f"ChaCha20 average encryption time: {chacha20_time:.6f} seconds")
    print(f"ChaCha20 standard deviation: {chacha20_std:.6f} seconds")
    print(f"ChaCha20 throughput: {chacha20_throughput:.2f} MB/s")
    print(f"CPU Usage: {chacha20_cpu_after}%")
    print(f"Battery Level: {chacha20_battery_after}%")
    save_to_csv(data_type, file_size, "ChaCha20", chacha20_time, chacha20_std, chacha20_throughput, chacha20_cpu_ambient, chacha20_battery_ambient, chacha20_cpu_after, chacha20_battery_after)
    benchmark_results = {
    "AES": {
        "encryption_time": aes_time,
        "throughput": aes_throughput,
        "cpu": aes_cpu_after
    },
    "PRESENT": {
        "encryption_time": present_time,
        "throughput": present_throughput,
        "cpu": present_cpu_after
    },
    "ChaCha20": {
        "encryption_time": chacha20_time,
        "throughput": chacha20_throughput,
        "cpu": chacha20_cpu_after
    }
}
    return benchmark_results, aes_battery_ambient
#main function to benchmark a specific file
def main():
    benchmark_file("data/sample_10KB.txt")
if __name__ == "__main__":
    main()