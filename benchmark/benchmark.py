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
    for _ in range(10):
        start = time.perf_counter()
        encrypt_function(input_file, output_file, key)
        end = time.perf_counter()
        elapsed = end - start
        times.append(elapsed)
    average_time = statistics.mean(times)
    standard_deviation = statistics.stdev(times)

    file_info = get_file_info(input_file)
    file_size = file_info["size_bytes"]
    file_size_mb = file_size / (1024 * 1024)
    throughput = file_size_mb / average_time
    cpu = get_cpu_usage()
    battery = get_battery_level()
    return average_time, standard_deviation, cpu, battery, throughput

def save_to_csv(data_type, file_size, algorithm, average_time, standard_deviation, throughput, cpu, battery):
    with open("ml/dataset.csv", "a", newline="") as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(["Data Type","File Size (Bytes)", "Algorithm", "Average Time (s)", "Standard Deviation (s)",
                             "Throughput (MB/s)", "CPU Usage (%)","Battery Level (%)" ])
        writer.writerow([data_type, file_size, algorithm, average_time, standard_deviation, throughput, cpu, battery])

def benchmark_file(input_file):
    file_info = get_file_info(input_file)
    data_type = file_info["data_type"]
    file_size = file_info["size_bytes"]
    output_file = input_file + ".enc"

    key_aes = os.urandom(16)
    key_present = int.from_bytes(os.urandom(10), "big")
    key_chacha20 = os.urandom(32)

    print("Benchmarking AES...")
    aes_time, aes_std, aes_cpu, aes_battery, aes_throughput = benchmark_algorithm(aes_encrypt, input_file, output_file, key_aes)
    
    print("Benchmarking PRESENT...")
    present_time, present_std ,present_cpu, present_battery, present_throughput = benchmark_algorithm(present_encrypt, input_file, output_file, key_present)
    
    print("Benchmarking ChaCha20...")
    chacha20_time, chacha20_std ,chacha20_cpu, chacha20_battery, chacha20_throughput= benchmark_algorithm(chacha20_encrypt, input_file, output_file, key_chacha20)
    #aes
    print(f"AES average encryption time: {aes_time:.6f} seconds")
    print(f"AES standard deviation: {aes_std:.6f} seconds")
    print(f"AES throughput: {aes_throughput:.2f} MB/s")
    print(f"CPU Usage: {aes_cpu}%")
    print(f"Battery Level: {aes_battery}%")
    save_to_csv(data_type, file_size, "AES", aes_time, aes_std, aes_throughput, aes_cpu, aes_battery)
    #present
    print(f"PRESENT average encryption time: {present_time:.6f} seconds")
    print(f"PRESENT standard deviation: {present_std:.6f} seconds")
    print(f"PRESENT throughput: {present_throughput:.2f} MB/s")
    print(f"CPU Usage: {present_cpu}%")
    print(f"Battery Level: {present_battery}%")
    save_to_csv(data_type, file_size, "PRESENT", present_time, present_std, present_throughput, present_cpu, present_battery)
    #chacha20
    print(f"ChaCha20 average encryption time: {chacha20_time:.6f} seconds")
    print(f"ChaCha20 standard deviation: {chacha20_std:.6f} seconds")
    print(f"ChaCha20 throughput: {chacha20_throughput:.2f} MB/s")
    print(f"CPU Usage: {chacha20_cpu}%")
    print(f"Battery Level: {chacha20_battery}%")
    save_to_csv(data_type, file_size, "ChaCha20", chacha20_time, chacha20_std, chacha20_throughput, chacha20_cpu, chacha20_battery)
#main function to benchmark a specific file
def main():
    benchmark_file("data/sample_1KB.txt")
if __name__ == "__main__":
    main()