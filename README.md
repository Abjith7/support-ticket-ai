# Support Ticket AI System

An AI-powered system for querying and analysing a customer support ticket dataset using natural language. Built for the DOTMappers AI Engineer Assessment.

---

## Architecture

```
support_tickets.csv
        │
        ▼
  app/data.py          ← Loads and parses CSV once at startup (pandas DataFrame)
        │
        ├──▶ app/query.py      ← NL question → Groq LLM → pandas expression → result
        │
        ├──▶ app/anomaly.py    ← Rule-based anomaly detection (z-score + SLA rules)
        │
        └──▶ app/main.py       ← FastAPI: /health, /query, /anomalies
```

**Key design decision:** The LLM does not answer questions directly from training knowledge. It generates a pandas expression which is evaluated against the real DataFrame. This ensures factual accuracy and makes the system auditable — every response includes the exact expression used.

---

## Model & Tools

| Component | Choice | Reason |
|---|---|---|
| LLM | Groq — llama3-70b-8192 | Free tier, fast inference, strong code generation |
| Data layer | pandas | 500-row CSV; no database overhead needed |
| API | FastAPI | Async, auto-docs at /docs, Pydantic validation |
| Anomaly detection | Rule-based (z-score + SLA thresholds) | Deterministic; no hallucination risk |

---

## Setup

**1. Clone and install**
```bash
git clone <repo-url>
cd ticket_system
pip install -r requirements.txt
```

**2. Set your API key**
```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

**3. Run**
```bash
uvicorn app.main:app --reload
```

API is live at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## Endpoints

### `GET /health`
Returns system status and dataset info.

```json
{
  "status": "ok",
  "total_tickets": 500,
  "columns": ["ticket_id", "created_at", ...]
}
```

---

### `POST /query`
Answer a natural language question about the ticket data.

**Request:**
```json
{ "question": "How many tickets are currently open?" }
```

**Response:**
```json
{
  "question": "How many tickets are currently open?",
  "answer": 173,
  "expression": "df[df['status'] == 'Open'].shape[0]"
}
```

**More example queries and outputs:**

| Query | Answer |
|---|---|
| "Which agent resolved the most tickets?" | `"AGT-05"` |
| "What is the average customer rating for Technical tickets?" | `3.87` |
| "Show me all Critical tickets not resolved within 12 hours" | `[{...}, ...]` |
| "How many tickets are escalated?" | `47` |

---

### `GET /anomalies`
Detects and returns flagged tickets based on three rules.

**Rules applied:**
1. **Slow resolution** — resolution time > 2.5 standard deviations above mean
2. **Stale high-priority** — High or Critical tickets unresolved for > 24 hours
3. **Critical SLA breach** — Critical tickets unresolved beyond 12 hours

**Response:**
```json
{
  "total_anomalies": 92,
  "breakdown": {
    "slow_resolution": 12,
    "stale_high_priority": 80,
    "critical_unresolved": 31
  },
  "anomalies": [
    {
      "ticket_id": "TKT-023",
      "priority": "Low",
      "resolution_time_hrs": 76.1,
      "anomaly_reason": "Resolution time 76.1h is abnormally high (mean=19.2h, std=20.0h)"
    }
  ]
}
```

---

## Known Limitations

- **Static data:** The CSV is loaded at startup. A file change requires a server restart.
- **LLM non-determinism on edge cases:** Although `temperature=0`, very ambiguous queries may produce incorrect pandas expressions. The `expression` field in responses allows manual verification.
- **No authentication:** The API has no auth layer. Not production-ready as-is.
- **"Now" is relative:** Anomaly detection uses the latest `created_at` in the dataset as the reference time, not wall-clock time. This is correct for historical data analysis.

---

## What I Would Improve With More Time

- Add a caching layer (Redis) for repeated NL queries
- Stream LLM responses for large result sets
- Add input guardrails to reject non-data questions before hitting the LLM
- Replace static CSV load with a proper database (PostgreSQL + SQLAlchemy)
- Add a minimal Streamlit UI alongside the API
