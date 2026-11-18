from typing import Any, Literal, Optional

from pydantic import BaseModel, field_validator, model_validator


class EvaluationRequest(BaseModel):
    cumulative_payload: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def accept_application(cls, body):
        if isinstance(body, dict) and body and "cumulative_payload" not in body:
            return {"cumulative_payload": body}
        return body

    @field_validator("cumulative_payload")
    @classmethod
    def flatten_fields(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Convert nested JSON objects to the dot paths used by the catalog."""
        fields = {}
        aliases = {"student.firstName": "studentInfo.firstName", "student.ssn": "studentInfo.ssn",
                   "parent.income": "income.parentIncome"}

        def visit(path: str, value: Any) -> None:
            path = aliases.get(path, path)
            if isinstance(value, dict) and value:
                for key, child in value.items():
                    visit(f"{path}.{key}", child)
            elif path in fields:
                raise ValueError(f"Duplicate field path: {path}")
            else:
                fields[path] = value

        for key, value in payload.items():
            visit(key, value)
        return fields


class SubmittedField(BaseModel):
    field_name: str
    status: Literal["VALID", "INVALID"]
    violation_message: Optional[str]
    rule_name: Optional[str]
    severity: Literal["ERROR"]


class BuildInfo(BaseModel):
    version: str


class EvaluationResponse(BaseModel):
    status: Literal["VALID", "INVALID", "INCOMPLETE"]
    submitted: list[SubmittedField]
    outstanding: list[str]
    info: BuildInfo
