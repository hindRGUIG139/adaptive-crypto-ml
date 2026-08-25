import os
import json
import csv
import random
import string
import wave
import struct

DATA_FOLDER = "data"

os.makedirs(DATA_FOLDER, exist_ok=True)


def create_binary_file(filename, size_mb):
    size = size_mb * 1024 * 1024

    with open(
        os.path.join(DATA_FOLDER, filename),
        "wb"
    ) as file:
        file.write(os.urandom(size))


def create_text_file(filename, size_kb):
    target_size = size_kb * 1024

    text = (
        "This is a test file for the Adaptive Crypto ML project. "
        "The file is used to benchmark AES-256, ChaCha20 and PRESENT. "
        "The system measures encryption time, throughput, CPU usage "
        "and battery level. "
    )

    with open(
        os.path.join(DATA_FOLDER, filename),
        "w",
        encoding="utf-8"
    ) as file:

        while file.tell() < target_size:
            file.write(text)


def create_csv_file(filename, size_kb):
    target_size = size_kb * 1024

    path = os.path.join(DATA_FOLDER, filename)

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "id",
            "name",
            "value",
            "category"
        ])

        i = 0

        while file.tell() < target_size:
            writer.writerow([
                i,
                f"user_{i}",
                random.randint(1, 100000),
                random.choice([
                    "A",
                    "B",
                    "C",
                    "D"
                ])
            ])

            i += 1


def create_json_file(filename, size_kb):
    target_size = size_kb * 1024

    data = []
    i = 0

    while len(
        json.dumps(data)
    ) < target_size:

        data.append({
            "id": i,
            "name": f"user_{i}",
            "value": random.randint(1, 100000),
            "category": random.choice([
                "A",
                "B",
                "C",
                "D"
            ])
        })

        i += 1

    with open(
        os.path.join(DATA_FOLDER, filename),
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file
        )


def create_xml_file(filename, size_kb):
    target_size = size_kb * 1024

    path = os.path.join(
        DATA_FOLDER,
        filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("<dataset>\n")

        i = 0

        while file.tell() < target_size:
            file.write(
                f"    <record>"
                f"<id>{i}</id>"
                f"<name>user_{i}</name>"
                f"<value>{random.randint(1, 100000)}</value>"
                f"</record>\n"
            )

            i += 1

        file.write("</dataset>")


def create_wav_file(filename, size_mb):
    sample_rate = 8000
    channels = 1
    sample_width = 2

    target_bytes = size_mb * 1024 * 1024

    frames = (
        target_bytes // sample_width
    )

    path = os.path.join(
        DATA_FOLDER,
        filename
    )

    with wave.open(path, "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(sample_width)
        audio.setframerate(sample_rate)

        for _ in range(frames):
            audio.writeframes(
                struct.pack("<h", 0)
            )


def create_docx_placeholder(filename, size_kb):
    """
    Creates a binary test file with a DOCX extension.
    It is suitable for encryption benchmarking,
    but it is NOT a valid Word document.
    """

    create_binary_file(
        filename,
        max(1, size_kb // 1024)
    )


def main():

    print("Generating test files...\n")

    # ---------------------------------
    # TEXT
    # ---------------------------------

    text_files = [
        ("sample_1KB.txt", 1),
        ("sample_10KB.txt", 10),
        ("sample_100KB.txt", 100),
        ("sample_1MB.txt", 1024),
        ("sample_5MB.txt", 5120),
        ("sample_10MB.txt", 10240),
    ]

    for filename, size in text_files:
        create_text_file(filename, size)
        print(f"Created {filename}")


    # ---------------------------------
    # CSV
    # ---------------------------------

    csv_files = [
        ("sample_100KB.csv", 100),
        ("sample_500KB.csv", 500),
        ("sample_1MB.csv", 1024),
    ]

    for filename, size in csv_files:
        create_csv_file(filename, size)
        print(f"Created {filename}")


    # ---------------------------------
    # JSON
    # ---------------------------------

    json_files = [
        ("sample_100KB.json", 100),
        ("sample_500KB.json", 500),
        ("sample_1MB.json", 1024),
    ]

    for filename, size in json_files:
        create_json_file(filename, size)
        print(f"Created {filename}")


    # ---------------------------------
    # XML
    # ---------------------------------

    xml_files = [
        ("sample_100KB.xml", 100),
        ("sample_500KB.xml", 500),
        ("sample_1MB.xml", 1024),
    ]

    for filename, size in xml_files:
        create_xml_file(filename, size)
        print(f"Created {filename}")


    # ---------------------------------
    # BINARY FILES
    # ---------------------------------

    binary_files = [
        ("sample_binary_1MB.bin", 1),
        ("sample_binary_5MB.bin", 5),
        ("sample_binary_10MB.bin", 10),
        ("sample_binary_20MB.bin", 20),
    ]

    for filename, size in binary_files:
        create_binary_file(filename, size)
        print(f"Created {filename}")


    # ---------------------------------
    # AUDIO
    # ---------------------------------

    audio_files = [
        ("sample_audio_1MB.wav", 1),
        ("sample_audio_5MB.wav", 5),
    ]

    for filename, size in audio_files:
        create_wav_file(filename, size)
        print(f"Created {filename}")


    print("\nFinished!")
    print(f"Files are located in: {DATA_FOLDER}/")


if __name__ == "__main__":
    main()