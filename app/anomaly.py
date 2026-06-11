# app/anomaly.py
 
import pandas as pd
from app.data import DF
 
RESOLUTION_ZSCORE_THRESHOLD = 2.5
HIGH_PRIORITY_UNRESOLVED_HRS = 24
CRITICAL_UNRESOLVED_HRS = 12
 
def _serialize(df: pd.DataFrame) -> list[dict]:
    df = df.copy()

    for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df[col] = df[col].astype(str)

    records = df.to_dict(orient="records")

    for record in records:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None

    return records
 
def detect_slow_resolution(df: pd.DataFrame) -> list[dict]:
    resolved = df[df["resolution_time_hrs"].notna()].copy()
    mean = resolved["resolution_time_hrs"].mean()
    std = resolved["resolution_time_hrs"].std()
    flagged = resolved[
        (resolved["resolution_time_hrs"] - mean) / std > RESOLUTION_ZSCORE_THRESHOLD
    ].copy()
    flagged["anomaly_reason"] = flagged["resolution_time_hrs"].apply(
        lambda x: f"Resolution time {x:.1f}h is abnormally high (mean={mean:.1f}h, std={std:.1f}h)"
    )
    return _serialize(flagged)
 
def detect_stale_high_priority(df: pd.DataFrame) -> list[dict]:
    now = df["created_at"].max()
    unresolved = df[df["status"].isin(["Open", "Escalated"])].copy()
    flagged = unresolved[
        (unresolved["priority"].isin(["High", "Critical"])) &
        ((now - unresolved["created_at"]).dt.total_seconds() / 3600 > HIGH_PRIORITY_UNRESOLVED_HRS)
    ].copy()
    flagged["anomaly_reason"] = flagged.apply(
        lambda r: f"{r['priority']} ticket unresolved for >{HIGH_PRIORITY_UNRESOLVED_HRS}h",
        axis=1,
    )
    return _serialize(flagged)
 
def detect_critical_unresolved(df: pd.DataFrame) -> list[dict]:
    now = df["created_at"].max()
    flagged = df[
        (df["priority"] == "Critical") &
        (df["status"] != "Resolved") &
        ((now - df["created_at"]).dt.total_seconds() / 3600 > CRITICAL_UNRESOLVED_HRS)
    ].copy()
    flagged["anomaly_reason"] = f"Critical ticket unresolved beyond {CRITICAL_UNRESOLVED_HRS}h SLA"
    return _serialize(flagged)
 
def run_all_anomalies() -> dict:
    slow = detect_slow_resolution(DF)
    stale = detect_stale_high_priority(DF)
    critical = detect_critical_unresolved(DF)
 
    seen = set()
    combined = []
    for record in slow + stale + critical:
        tid = record["ticket_id"]
        if tid not in seen:
            seen.add(tid)
            combined.append(record)
 
    return {
        "total_anomalies": len(combined),
        "breakdown": {
            "slow_resolution": len(slow),
            "stale_high_priority": len(stale),
            "critical_unresolved": len(critical),
        },
        "anomalies": combined,
    }
 