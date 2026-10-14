from pydantic import BaseModel, Field, field_validator


class LeadQualification(BaseModel):
    score: int = Field(ge=1, le=10)
    reasons: list[str] = Field(min_length=1)
    evidence: list[str] = Field(min_length=1)
    qualified: bool

    @field_validator("reasons", "evidence")
    @classmethod
    def values_must_not_be_empty(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty item is required.")
        return cleaned
