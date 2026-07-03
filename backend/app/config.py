from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cognee_base_url: str
    cognee_api_key: str
    # LLM — supports OpenAI, Gemini (via LiteLLM), or any LiteLLM-compatible provider
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    # Set to "true" to skip the LLM connection test on startup
    cognee_skip_connection_test: str = "false"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_file_ignore_empty = True


settings = Settings()
