from pydantic import BaseSettings


class Settings(BaseSettings):
    API_TOKEN:str
    MONGODB_URL:str

    class Config:
        env_file = '.env'

settings = Settings()
