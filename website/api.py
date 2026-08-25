import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the saved dictionary bundle
bundle = joblib.load("ml/predictor.joblib")

model = bundle["model"]
data_type_encoder = bundle["data_type_encoder"]
print("Valid data types:", data_type_encoder.classes_)
algorithms_encoder = bundle["algorithms_encoder"]
feature_order = bundle["feature_order"]


class CryptoRequest(BaseModel):
    file_type: str
    file_size: float  # Value sent from UI in KB
    cpu_usage: float
    battery_level: float


@app.post("/predict")
def predict_algorithm(data: CryptoRequest):

    print("Received file_type:", repr(data.file_type))
    print("Valid types:", list(data_type_encoder.classes_))
    # 1. Encode "Data Type" string using the fitted LabelEncoder
    try:
        encoded_data_type = data_type_encoder.transform([data.file_type])[0]
    except ValueError:
        valid_types = list(data_type_encoder.classes_)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown Data Type '{data.file_type}'. Valid choices: {valid_types}",
        )

    # 2. Convert KB input to Bytes and apply np.log1p as done during training
    file_size_bytes = data.file_size * 1024
    log_file_size = np.log1p(file_size_bytes)

    # 3. Format DataFrame matching exact feature column names and order
    features = pd.DataFrame(
        [
            {
                "Data Type": encoded_data_type,
                "File Size (Bytes)": log_file_size,
                "CPU Ambient (%)": data.cpu_usage,
                "Battery Ambient (%)": data.battery_level,
            }
        ]
    )[feature_order]

    # 4. Predict integer class ID
    prediction_id = model.predict(features)[0]

    # 5. Decode integer back to algorithm string name (e.g., "ChaCha20")
    algo_name = algorithms_encoder.inverse_transform([prediction_id])[0]

    return {
        "recommended_algorithm": str(algo_name),
        "model_used": bundle.get("model_name", "unknown"),
    }