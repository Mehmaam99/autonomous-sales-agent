from pydantic import BaseModel, Field, field_validator


class AgentPolicy(BaseModel):
    dry_run: bool = True
    require_human_approval: bool = True


class OutreachPolicy(BaseModel):
    max_followups: int = Field(ge=0)
    followup_interval_days: int = Field(gt=0)


class EmailPolicy(BaseModel):
    max_recipients_per_run: int = Field(gt=0)


class SafetyPolicy(BaseModel):
    stop_on_unsubscribe: bool = True
    stop_on_policy_violation: bool = True


class PoliciesConfig(BaseModel):
    agent: AgentPolicy
    outreach: OutreachPolicy
    email: EmailPolicy
    safety: SafetyPolicy


class RetrievalSettings(BaseModel):
    top_k: int = Field(gt=0)
    similarity_threshold: float = Field(ge=0.0, le=1.0)


class ChunkingSettings(BaseModel):
    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)


class SearchSettings(BaseModel):
    semantic: bool = True
    keyword: bool = True


class RetrievalConfig(BaseModel):
    retrieval: RetrievalSettings
    chunking: ChunkingSettings
    search: SearchSettings


class EmailOutreachSettings(BaseModel):
    max_length: int = Field(gt=0)
    tone: str
    include_unsubscribe: bool = True


class FollowupSettings(BaseModel):
    enabled: bool = True
    max_attempts: int = Field(ge=0)
    delay_days: int = Field(gt=0)


class PersonalizationSettings(BaseModel):
    required: bool = True
    minimum_evidence_points: int = Field(ge=0)


class OutreachConfig(BaseModel):
    email: EmailOutreachSettings
    followup: FollowupSettings
    personalization: PersonalizationSettings


class NicheInfo(BaseModel):
    name: str
    display_name: str


class IdealCustomerProfile(BaseModel):
    business_types: list[str]
    minimum_business_size: str


class QualificationConfig(BaseModel):
    minimum_score: int = Field(ge=1, le=10)
    weights: dict[str, float]

    @field_validator("weights")
    @classmethod
    def weights_must_sum_to_one(cls, value: dict[str, float]) -> dict[str, float]:
        if not value:
            raise ValueError("qualification weights cannot be empty")

        if any(weight < 0 for weight in value.values()):
            raise ValueError("qualification weights cannot be negative")

        if abs(sum(value.values()) - 1.0) > 1e-6:
            raise ValueError("qualification weights must sum to 1.0")

        return value


class OfferConfig(BaseModel):
    name: str
    value_proposition: str


class NicheConfig(BaseModel):
    niche: NicheInfo
    ideal_customer_profile: IdealCustomerProfile
    pain_points: list[str]
    qualification: QualificationConfig
    offer: OfferConfig
 
class AppSettings(BaseModel):
    name: str
    version: str
    environment: str


class LLMConfig(BaseModel):
    provider: str
    models: dict[str, str]
    generation: dict[str, int | float]


class ApplicationConfig(BaseModel):
    app: AppSettings
    llm: LLMConfig
    policies: PoliciesConfig
    retrieval: RetrievalConfig
    outreach: OutreachConfig
    niche: NicheConfig
