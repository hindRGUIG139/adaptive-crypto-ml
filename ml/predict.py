import os
import sys
import joblib
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from monitoring.file_info import get_file_info
from monitoring.system_metrics import get_cpu_usage, get_battery_level

model = joblib.load(os.path.join(PROJECT_ROOT, "ml", "best_model.pkl"))
data_type_encoder = joblib.load(os.path.join(PROJECT_ROOT, "ml", "data_type_encoder.pkl"))
algorithm_encoder = joblib.load(os.path.join(PROJECT_ROOT, "ml", "algorithm_encoder.pkl"))

def predict_algorithm(file_path):
    file_info = get_file_info(file_path)
    data_type = file_info["data_type"]
    file_size = file_info["size_bytes"]

    cpu = get_cpu_usage()
    battery = get_battery_level()

    data_type_encoded = data_type_encoder.transform([data_type])[0]

    X = pd.DataFrame([{
        "Data Type": data_type_encoded,
        "File Size (Bytes)": file_size,
        "CPU Ambient (%)": cpu,
        "Battery Ambient (%)": battery
    }])

    prediction = model.predict(X)[0]
    algorithm = algorithm_encoder.inverse_transform([prediction])[0]

    print(f"File: {os.path.basename(file_path)}")
    print(f"Data Type: {data_type}")
    print(f"File Size: {file_size} bytes")
    print(f"CPU: {cpu}%")
    print(f"Battery: {battery}%")
    print(f"Selected Algorithm: {algorithm}")

    return algorithm

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m ml.predict <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    predict_algorithm(file_path)