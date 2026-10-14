from pydantic import BaseModel, Field, model_validator


class AppSettings(BaseModel):
    name: str
    version: str
    environment: str


class LLMGenerationConfig(BaseModel):
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(gt=0)


class LLMConfig(BaseModel):
    provider: str
    models: dict[str, str]
    generation: LLMGenerationConfig


class AgentPolicyConfig(BaseModel):
    dry_run: bool
    require_human_approval: bool


class OutreachPolicyConfig(BaseModel):
    max_followups: int = Field(ge=0)
    followup_interval_days: int = Field(gt=0)


class EmailPolicyConfig(BaseModel):
    max_recipients_per_run: int = Field(gt=0)


class SafetyPolicyConfig(BaseModel):
    stop_on_unsubscribe: bool
    stop_on_policy_violation: bool


class PoliciesConfig(BaseModel):
    agent: AgentPolicyConfig
    outreach: OutreachPolicyConfig
    email: EmailPolicyConfig
    safety: SafetyPolicyConfig


class RetrievalConfig(BaseModel):
    model_config = {"extra": "allow"}


class OutreachConfig(BaseModel):
    model_config = {"extra": "allow"}


class NicheDetails(BaseModel):
    name: str
    display_name: str


class IdealCustomerProfile(BaseModel):
    business_types: list[str]
    minimum_business_size: str


class QualificationConfig(BaseModel):
    minimum_score: int = Field(ge=1, le=10)
    weights: dict[str, float]

    @model_validator(mode="after")
    def validate_weights_sum(self):
        if any(weight < 0 or weight > 1 for weight in self.weights.values()):
            raise ValueError("Qualification weights must be between 0 and 1.")

        if abs(sum(self.weights.values()) - 1.0) > 1e-6:
            raise ValueError("Qualification weights must sum to 1.0.")

        return self


class OfferConfig(BaseModel):
    name: str
    value_proposition: str


class NicheConfig(BaseModel):
    niche: NicheDetails
    ideal_customer_profile: IdealCustomerProfile
    pain_points: list[str]
    qualification: QualificationConfig
    offer: OfferConfig


class ApplicationConfig(BaseModel):
    app: AppSettings
    llm: LLMConfig
    policies: PoliciesConfig
    retrieval: RetrievalConfig
    outreach: OutreachConfig
    niche: NicheConfig
