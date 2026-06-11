# app/main.py
 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.query import answer_query
from app.anomaly import run_all_anomalies
from app.data import DF
 
app = FastAPI(
    title="Support Ticket AI System",
    description="NL querying and anomaly detection over customer support tickets.",
    version="1.0.0",
)
 
 
class QueryRequest(BaseModel):
    question: str
 
 
# Health Check
@app.get("/health")
def health():
    return {
        "status": "ok",
        "total_tickets": len(DF),
        "columns": DF.columns.tolist(),
    }
 
 
# Natural Language Query
@app.post("/query")
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    result = answer_query(request.question)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
 
 
# Anomaly Detection
@app.get("/anomalies")
def anomalies():
    return run_all_anomalies()