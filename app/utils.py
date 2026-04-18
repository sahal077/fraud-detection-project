import os
import uuid
import pandas as pd
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
REQUIRED_COLUMNS = {
    "transaction_id",
    "amount",
    "timestamp",
    "merchant_category",
    "location",
    "user_id",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, upload_folder):
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(upload_folder, secure_filename(unique_name))
    file.save(path)
    return path


def read_transaction_file(filepath):
    ext = filepath.rsplit(".", 1)[1].lower()
    if ext == "csv":
        df = pd.read_csv(filepath)
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return df


def validate_dataframe(df):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return False, f"Missing required columns: {', '.join(sorted(missing))}"

    if df.empty:
        return False, "File contains no data rows"

    try:
        pd.to_datetime(df["timestamp"])
    except Exception:
        return False, "Column 'timestamp' contains invalid date values"

    try:
        df["amount"].astype(float)
    except Exception:
        return False, "Column 'amount' contains non-numeric values"

    return True, "OK"


def compute_stats(df):
    total = len(df)
    anomaly_count = int(df["is_anomaly"].sum()) if "is_anomaly" in df.columns else 0
    anomaly_pct = round(anomaly_count / total * 100, 2) if total > 0 else 0
    total_amount = round(float(df["amount"].sum()), 2)
    avg_amount = round(float(df["amount"].mean()), 2)
    anomaly_amount = (
        round(float(df.loc[df["is_anomaly"], "amount"].sum()), 2)
        if "is_anomaly" in df.columns
        else 0
    )

    return {
        "total_transactions": total,
        "anomaly_count": anomaly_count,
        "anomaly_pct": anomaly_pct,
        "total_amount": total_amount,
        "avg_amount": avg_amount,
        "anomaly_amount": anomaly_amount,
    }
