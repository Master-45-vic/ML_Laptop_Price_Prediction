from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import math

# ---------------- LOAD ARTIFACTS ---------------- #
model = joblib.load("xgb_price_model.pkl")
encoder = joblib.load("encoder.pkl")
scaler = joblib.load("scaler.pkl")

# ---------------- FASTAPI APP ---------------- #
app = FastAPI(title="Laptop Price Prediction API")

# ---------------- INPUT SCHEMA ---------------- #
class LaptopInput(BaseModel):
    Brand: str
    Model: str
    CPU: str
    GPU: str | None = "Others"
    Storage_type: str
    Touch: str
    Status: str
    RAM: int
    Storage: int
    Screen: float


# ---------------- PREDICT ENDPOINT ---------------- #
@app.post("/predict")
def predict_price(data: LaptopInput):

    # Convert input to DataFrame
    input_df = pd.DataFrame([data.dict()])

    # Column names (must match training)
    cat_cols = ['Brand', 'Model', 'CPU', 'GPU', 'Storage type', 'Touch', 'Status']
    num_cols = ['RAM', 'Storage', 'Screen']

    # Rename if required
    input_df.rename(columns={"Storage_type": "Storage type"}, inplace=True)

    try:
        # Fill missing GPU
        input_df["GPU"] = input_df["GPU"].fillna("Others")

        # Split features
        X_cat = input_df[cat_cols]
        X_num = input_df[num_cols]

        # Encode categorical
        X_cat_enc = encoder.transform(X_cat)

        # Scale numeric
        X_num_scaled = scaler.transform(X_num)

        # Combine features
        X_final = np.hstack([X_cat_enc, X_num_scaled])

        # Predict (log target → revert)
        log_price = model.predict(X_final)
        price = math.floor(np.expm1(log_price)[0])

        return {
            "predicted_price_usd": price
        }

    except Exception as e:
        return {
            "error": "Prediction failed",
            "details": str(e)
        }
