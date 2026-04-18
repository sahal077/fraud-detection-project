import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler


def detect_anomalies(df, method="isolation_forest", contamination=0.05):
    """Run anomaly detection on a DataFrame of transactions.

    Args:
        df: DataFrame with columns amount, timestamp, merchant_category, location, user_id
        method: 'isolation_forest', 'one_class_svm', 'zscore', or 'iqr'
        contamination: expected fraction of anomalies (0-1)

    Returns:
        DataFrame with added columns: is_anomaly, anomaly_score
    """
    df = df.copy()
    features = _build_features(df)

    if method == "isolation_forest":
        df = _isolation_forest(df, features, contamination)
    elif method == "one_class_svm":
        df = _one_class_svm(df, features, contamination)
    elif method == "zscore":
        df = _zscore_detection(df, threshold=3.0)
    elif method == "iqr":
        df = _iqr_detection(df, multiplier=1.5)
    else:
        raise ValueError(f"Unknown method: {method}")

    return df


def _build_features(df):
    """Engineer numeric features from raw transaction data."""
    features = pd.DataFrame()
    features["amount"] = df["amount"].astype(float)

    ts = pd.to_datetime(df["timestamp"])
    features["hour"] = ts.dt.hour
    features["day_of_week"] = ts.dt.dayofweek
    features["day_of_month"] = ts.dt.day

    cat_encoded = df["merchant_category"].astype("category").cat.codes
    features["merchant_cat"] = cat_encoded

    loc_encoded = df["location"].astype("category").cat.codes
    features["location_enc"] = loc_encoded

    features["amount_log"] = np.log1p(features["amount"].abs())

    if "user_id" in df.columns:
        user_mean = df.groupby("user_id")["amount"].transform("mean")
        user_std = df.groupby("user_id")["amount"].transform("std").fillna(1)
        features["amount_zscore_user"] = (df["amount"] - user_mean) / user_std.replace(
            0, 1
        )

    features = features.fillna(0)
    return features


def _isolation_forest(df, features, contamination):
    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    model = IsolationForest(
        contamination=contamination,
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    scores = -model.score_samples(X)
    scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)

    df["anomaly_score"] = scores
    df["is_anomaly"] = model.predict(X) == -1
    return df


def _one_class_svm(df, features, contamination):
    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    nu = max(contamination, 0.01)
    model = OneClassSVM(kernel="rbf", gamma="scale", nu=nu)
    model.fit(X)

    scores = -model.decision_function(X)
    scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)

    df["anomaly_score"] = scores
    df["is_anomaly"] = model.predict(X) == -1
    return df


def _zscore_detection(df, threshold=3.0):
    amounts = df["amount"].astype(float)
    mean = amounts.mean()
    std = amounts.std() if amounts.std() > 0 else 1
    z = ((amounts - mean) / std).abs()

    df["anomaly_score"] = z / (z.max() + 1e-8)
    df["is_anomaly"] = z > threshold
    return df


def _iqr_detection(df, multiplier=1.5):
    amounts = df["amount"].astype(float)
    q1 = amounts.quantile(0.25)
    q3 = amounts.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    outlier_dist = amounts.apply(
        lambda x: max(0, x - upper) if x > upper else max(0, lower - x)
    )
    max_dist = outlier_dist.max() if outlier_dist.max() > 0 else 1

    df["anomaly_score"] = outlier_dist / max_dist
    df["is_anomaly"] = (amounts < lower) | (amounts > upper)
    return df
