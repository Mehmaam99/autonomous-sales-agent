import argparse

from app.db.session import SessionLocal
from app.qualification.workflow import LeadQualificationWorkflow


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run lead qualification and save the result."
    )
    parser.add_argument("--lead-id", type=int, required=True)
    parser.add_argument("--niche", default="real_estate")
    args = parser.parse_args()

    with SessionLocal() as session:
        result = LeadQualificationWorkflow(
            session,
            args.niche,
        ).run(args.lead_id)

        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
