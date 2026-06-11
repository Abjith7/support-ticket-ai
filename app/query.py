# app/query.py
 
import os
import traceback
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from app.data import DF
 
load_dotenv()
 
client = Groq(api_key=os.environ["GROQ_API_KEY"])
 
SCHEMA_DESCRIPTION = """
DataFrame name: df
Columns:
- ticket_id (str): Unique ticket identifier e.g. TKT-001
- created_at (datetime): Ticket creation timestamp
- category (str): One of ['Billing', 'Technical', 'General']
- priority (str): One of ['Low', 'Medium', 'High', 'Critical']
- status (str): One of ['Open', 'Resolved', 'Escalated']
- response_time_hrs (float): Hours from creation to first response
- resolution_time_hrs (float): Hours to resolve; NaN if unresolved
- agent_id (str): Assigned agent e.g. AGT-04
- customer_rating (float): Rating 1–5; NaN if unresolved
- issue_summary (str): Free text description
 
Sample rows:
ticket_id | created_at          | category | priority | status   | response_time_hrs | resolution_time_hrs | agent_id | customer_rating | issue_summary
TKT-001   | 2024-02-05 11:14:00 | General  | Low      | Resolved | 3.7               | 7.8                 | AGT-03   | 4.0             | Request for product documentation
TKT-002   | 2024-03-05 17:01:00 | Billing  | Low      | Resolved | 1.2               | 13.7                | AGT-09   | 4.0             | Incorrect charge on invoice
"""
 
SYSTEM_PROMPT = f"""You are a data analyst assistant. You have access to a pandas DataFrame called `df`.
 
{SCHEMA_DESCRIPTION}
 
When the user asks a question, respond ONLY with a single Python expression using pandas that answers it.
Rules:
- Output only the expression, no explanation, no markdown, no backticks.
- The expression must evaluate to a scalar, a list, a dict, or a small DataFrame.
- Do not use print(), do not assign variables.
- For counting use .shape[0] or len().
- For averages use .mean() and round to 2 decimal places with round().
- If the question involves agents and "most" or "best", return the agent_id as a string.
- Never import anything; pandas (pd) is already available.
- If the question cannot be answered from this data, respond with the string: CANNOT_ANSWER
"""
 
def _safe_eval(expr: str, df: pd.DataFrame):
    allowed_globals = {"df": df, "pd": pd}
    return eval(expr, {"__builtins__": {}}, allowed_globals)
 
def answer_query(question: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0,
            max_tokens=200,
        )
 
        expr = response.choices[0].message.content.strip()
 
        if expr == "CANNOT_ANSWER":
            return {"question": question, "answer": "This question cannot be answered from the available data.", "expression": None}
 
        result = _safe_eval(expr, DF)
 
        if isinstance(result, pd.DataFrame):
            answer = result.to_dict(orient="records")
        elif isinstance(result, pd.Series):
            answer = result.to_dict()
        else:
            answer = result
 
        return {"question": question, "answer": answer, "expression": expr}
 
    except Exception:
        return {"question": question, "answer": "Failed to process query.", "error": traceback.format_exc()}