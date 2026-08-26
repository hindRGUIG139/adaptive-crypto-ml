import joblib
import numpy as np
import pandas as pd
import os
import tempfile

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Your encryption implementations
from crypto_algorithms import aes
from crypto_algorithms import chacha20
from crypto_algorithms import present


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOAD ML MODEL
# ============================================================

bundle = joblib.load("ml/predictor.joblib")

model = bundle["model"]
data_type_encoder = bundle["data_type_encoder"]
algorithms_encoder = bundle["algorithms_encoder"]
feature_order = bundle["feature_order"]

print("Valid data types:", data_type_encoder.classes_)


# ============================================================
# KEYS
# ============================================================

# AES-256 = 32 bytes
AES_KEY = os.urandom(32)

# ChaCha20 = 32 bytes
CHACHA20_KEY = os.urandom(32)

# PRESENT-80 = 10 bytes = 80 bits
PRESENT_KEY = int.from_bytes(
    os.urandom(10),
    "big"
)


# ============================================================
# PREDICTION REQUEST
# ============================================================

class CryptoRequest(BaseModel):
    file_type: str
    file_size: float
    cpu_usage: float
    battery_level: float


# ============================================================
# PREDICTION
# ============================================================

@app.post("/predict")
def predict_algorithm(data: CryptoRequest):

    print("Received file_type:", repr(data.file_type))
    print("Valid types:", list(data_type_encoder.classes_))

    try:
        encoded_data_type = data_type_encoder.transform(
            [data.file_type]
        )[0]

    except ValueError:

        valid_types = list(data_type_encoder.classes_)

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown Data Type '{data.file_type}'. "
                f"Valid choices: {valid_types}"
            ),
        )


    # KB → Bytes
    file_size_bytes = data.file_size * 1024

    # Same transformation used during training
    log_file_size = np.log1p(file_size_bytes)


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


    prediction_id = model.predict(features)[0]

    algo_name = algorithms_encoder.inverse_transform(
        [prediction_id]
    )[0]


    print("Predicted algorithm:", algo_name)


    return {
        "recommended_algorithm": str(algo_name),
        "model_used": bundle.get(
            "model_name",
            "unknown"
        ),
    }


# ============================================================
# ENCRYPT
# ============================================================

@app.post("/encrypt")
async def encrypt_file(
    file: UploadFile = File(...),
    algorithm: str = Form(...)
):

    print("Encryption request:")
    print("Algorithm:", algorithm)
    print("Filename:", file.filename)


    # --------------------------------------------------------
    # Create temporary input file
    # --------------------------------------------------------

    input_suffix = os.path.splitext(
        file.filename
    )[1]

    input_path = tempfile.mktemp(
        suffix=input_suffix
    )

    output_path = tempfile.mktemp(
        suffix=".enc"
    )


    try:

        # Save uploaded file
        contents = await file.read()

        with open(input_path, "wb") as f:
            f.write(contents)


        # ----------------------------------------------------
        # Select YOUR encryption implementation
        # ----------------------------------------------------

        if algorithm in ("AES", "AES-256"):

            print("Using YOUR AES implementation")

            aes.encrypt_file(
                input_path,
                output_path,
                AES_KEY
            )


        elif algorithm == "ChaCha20":

            print("Using YOUR ChaCha20 implementation")

            chacha20.encrypt_file(
                input_path,
                output_path,
                CHACHA20_KEY
            )


        elif algorithm in ("PRESENT", "PRESENT-80"):

            print("Using YOUR PRESENT implementation")

            present.encrypt_file(
                input_path,
                output_path,
                PRESENT_KEY
            )


        else:

            raise HTTPException(
                status_code=400,
                detail=f"Unknown algorithm: {algorithm}"
            )


        # ----------------------------------------------------
        # Return encrypted file
        # ----------------------------------------------------

        return FileResponse(
            output_path,
            media_type="application/octet-stream",
            filename=file.filename + ".enc"
        )


    except HTTPException:
        raise

    except Exception as e:

        print("Encryption error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Encryption failed: {str(e)}"
        )

    finally:

        # We cannot delete output_path immediately because
        # FileResponse still needs it.
        #
        # The temporary files can be cleaned later.
        try:
            os.remove(input_path)
        except:
            pass


# ============================================================
# DECRYPT
# ============================================================

@app.post("/decrypt")
async def decrypt_file(
    file: UploadFile = File(...),
    algorithm: str = Form(...)
):

    print("Decryption request:")
    print("Algorithm:", algorithm)
    print("Filename:", file.filename)


    input_path = tempfile.mktemp(
        suffix=".enc"
    )

    output_path = tempfile.mktemp(
        suffix=".decrypted"
    )


    try:

        # Save encrypted file
        contents = await file.read()

        with open(input_path, "wb") as f:
            f.write(contents)


        # ----------------------------------------------------
        # YOUR AES
        # ----------------------------------------------------

        if algorithm in ("AES", "AES-256"):

            print("Using YOUR AES decryption")

            aes.decrypt_file(
                input_path,
                output_path,
                AES_KEY
            )


        # ----------------------------------------------------
        # YOUR CHACHA20
        # ----------------------------------------------------

        elif algorithm == "ChaCha20":

            print("Using YOUR ChaCha20 decryption")

            chacha20.decrypt_file(
                input_path,
                output_path,
                CHACHA20_KEY
            )


        # ----------------------------------------------------
        # YOUR PRESENT
        # ----------------------------------------------------

        elif algorithm in ("PRESENT", "PRESENT-80"):

            print("Using YOUR PRESENT decryption")

            present.decrypt_file(
                input_path,
                output_path,
                PRESENT_KEY
            )


        else:

            raise HTTPException(
                status_code=400,
                detail=f"Unknown algorithm: {algorithm}"
            )


        # ----------------------------------------------------
        # Return decrypted file
        # ----------------------------------------------------

        original_name = file.filename

        if original_name.endswith(".enc"):
            original_name = original_name[:-4]

        return FileResponse(
            output_path,
            media_type="application/octet-stream",
            filename=original_name
        )


    except HTTPException:
        raise

    except Exception as e:

        print("Decryption error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Decryption failed: {str(e)}"
        )

    finally:

        try:
            os.remove(input_path)
        except:
            pass