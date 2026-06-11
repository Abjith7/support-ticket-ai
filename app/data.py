# app/data.py
 
import pandas as pd
from pathlib import Path
 
DATA_PATH = Path(__file__).parent.parent / "support_tickets.csv"
 
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["resolution_time_hrs"] = pd.to_numeric(df["resolution_time_hrs"], errors="coerce")
    df["customer_rating"] = pd.to_numeric(df["customer_rating"], errors="coerce")
    df["response_time_hrs"] = pd.to_numeric(df["response_time_hrs"], errors="coerce")
    return df
 
DF: pd.DataFrame = load_data()
