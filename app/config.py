from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    API_TOKEN: str
    DB_PATH: str
    ADMIN_ID: int

    class Config:
        env_file = ".env"

settings = Settings()
