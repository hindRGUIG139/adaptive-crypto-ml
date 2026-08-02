import os #interact with the operating system
import statistics
import time
from crypto_algorithms.aes import encrypt_file as aes_encrypt
from crypto_algorithms.present import encrypt_file as present_encrypt
from crypto_algorithms.chacha20 import encrypt_file as chacha20_encrypt
import sys

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

    return average_time, standard_deviation

def main():
    input_file = "data/sample_100KB.txt"
    output_file = "data/sample_100KB.enc"
    key_aes = os.urandom(16)  # 128-bit key for AES
    key_present = int.from_bytes(os.urandom(10), "big")  # 80-bit key for PRESENT
    key_chacha20= os.urandom(32)  # 256-bit key for ChaCha20
    print("Benchmarking AES...")
    aes_time, aes_std = benchmark_algorithm(aes_encrypt, input_file, output_file, key_aes)

    print("Benchmarking PRESENT...")
    present_time, present_std = benchmark_algorithm(present_encrypt, input_file, output_file, key_present)
    print("Benchmarking ChaCha20...")
    chacha20_time, chacha20_std = benchmark_algorithm(chacha20_encrypt, input_file, output_file, key_chacha20)

    print(f"AES average encryption time: {aes_time:.6f} seconds")
    print(f"AES standard deviation: {aes_std:.6f} seconds")

    print(f"PRESENT average encryption time: {present_time:.6f} seconds")
    print(f"PRESENT standard deviation: {present_std:.6f} seconds")

    print(f"ChaCha20 average encryption time: {chacha20_time:.6f} seconds")
    print(f"ChaCha20 standard deviation: {chacha20_std:.6f} seconds")

if __name__ == "__main__":
    main()