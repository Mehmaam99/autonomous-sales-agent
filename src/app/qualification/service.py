import json

from app.core.config import load_application_config
from app.core.llm_gateway import LLMGateway
from app.qualification.prompts import SYSTEM_PROMPT
from app.qualification.schemas import LeadQualification


class LeadQualificationService:
    """Evaluate business leads using configured niche criteria and an LLM."""

    def __init__(self, niche: str) -> None:
        self.config = load_application_config(niche)
        self.gateway = LLMGateway(niche)

    def qualify(self, lead_data: dict[str, str]) -> LeadQualification:
        """Score a lead using supplied facts and return validated results."""
        if not lead_data:
            raise ValueError("Lead data must not be empty.")

        if not any(
            isinstance(value, str) and value.strip()
            for value in lead_data.values()
        ):
            raise ValueError("Lead data must contain at least one non-empty value.")

        niche_config = self.config.niche

        criteria = {
            "niche": niche_config.niche.model_dump(),
            "ideal_customer_profile": (
                niche_config.ideal_customer_profile.model_dump()
            ),
            "pain_points": niche_config.pain_points,
            "qualification": niche_config.qualification.model_dump(),
            "offer": niche_config.offer.model_dump(),
        }

        prompt = (
            "Evaluate this business lead using the configured criteria.\n\n"
            "CONFIGURATION:\n"
            f"{json.dumps(criteria, indent=2)}\n\n"
            "LEAD INFORMATION:\n"
            f"{json.dumps(lead_data, indent=2)}\n\n"
            "Return only the requested JSON object. Use only evidence "
            "present in the lead information. Do not invent missing facts."
        )

        response = self.gateway.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
        )

        result = LeadQualification.model_validate_json(response)

        minimum_score = niche_config.qualification.minimum_score
        expected_decision = result.score >= minimum_score

        if result.qualified != expected_decision:
            raise ValueError(
                "LLM qualification decision does not match the configured "
                f"minimum score of {minimum_score}."
            )

        return result
