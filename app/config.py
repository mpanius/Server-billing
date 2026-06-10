from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Server Billing Manager"
    database_path: str = "./data/server_billing.db"
    base_url: str = "http://127.0.0.1:8000"
    caddy_site_address: str = ":80"
    caddy_email: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    reminder_days: str = "7,3,1,0,-1"
    check_interval_seconds: int = 86400

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
