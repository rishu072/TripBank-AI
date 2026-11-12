from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60
    database_url: str = "mongodb://localhost:27017"
    database_name: str = "tripbank"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_base_url: str = "https://api-m.sandbox.paypal.com"
    paypal_webhook_id: str = ""
    paypal_merchant_id: str = ""
    default_currency: str = "USD"
    max_contribution_minor: int = 10000000
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""


settings = Settings()
