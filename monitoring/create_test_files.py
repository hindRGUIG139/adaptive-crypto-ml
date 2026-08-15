import os

files = {
    "sample_1KB.txt": 1_024,
    "sample_1KB2.txt": 1_024,
    "sample_1KB3.txt": 1_024,
    "sample_1KB4.txt": 1_024,
    "sample_10KB.txt": 10_240,
    "sample_10KB2.txt": 10_240,
    "sample_10KB3.txt": 10_240,
    "sample_10KB4.txt": 10_240,
    "sample_100KB.txt": 102_400,
    "sample_100KB2.txt": 102_400,
    "sample_100KB3.txt": 102_400,
    "sample_100KB4.txt": 102_400,
    "sample_1MB.txt": 1_048_576,
}

files_1= {
    "sample_1MB2.txt": 1_048_576,
    "sample_1MB3.txt": 1_048_576,
    "sample_1MB4.txt": 1_048_576
}

# Create each file with random data
for filename, size in files_1.items():
    with open(f"data/{filename}", "wb") as file:
        file.write(os.urandom(size))

print("Test files created successfully!")