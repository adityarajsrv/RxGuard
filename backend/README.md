# RxGuard — Backend

FastAPI service. See the root README for architecture and design rationale.

## Setup
```bash
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # add SERPAPI_KEY and GEMINI_API_KEY
uvicorn main:app --reload
```
Runs on `http://localhost:8000`. Interactive API docs at `/docs`.

## Tests
```bash
python tests/test_confidence_engine.py
python tests/test_interaction_checker.py
```