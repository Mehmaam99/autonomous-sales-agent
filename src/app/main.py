from app.core.config import load_yaml
from app.core.settings import settings


def main() -> None:
    app_config = load_yaml("app.yaml")
    llm_config = load_yaml("llm.yaml")

    print(f"Environment: {settings.app_env}")
    print(f"Application: {app_config['app']['name']}")
    print(f"LLM Provider: {llm_config['provider']}")
    print(f"Default Model: {llm_config['models']['default']}")


if __name__ == "__main__":
    main()