from fastapi import FastAPI

from api.schemas import EvaluationRequest, EvaluationResponse
from core.engine import evaluate_fafsa_payload

app = FastAPI(title="FAFSA Rule Processor")


@app.post("/api/v1/fafsa/evaluate", response_model=EvaluationResponse)
def evaluate_form(request: EvaluationRequest):
    return evaluate_fafsa_payload(request.cumulative_payload)
