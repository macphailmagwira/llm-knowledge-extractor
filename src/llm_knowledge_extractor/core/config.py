from os import environ

from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables from .env file
load_dotenv()


class Settings:
    APP_TITLE = environ.get("APP_TITLE")
    DEBUG = environ.get("DEBUG").lower() in ("true", "1", "t", "yes")
    ALLOWED_HOST = environ.get("ALLOWED_HOST")
    ALLOWED_PORT = int(environ.get("ALLOWED_PORT"))
    DB_USER = environ.get("POSTGRES_USER")
    DB_PASSWORD = environ.get("POSTGRES_PASSWORD")
    DB_DB = environ.get("POSTGRES_DB")
    DB_PORT = int(environ.get("POSTGRES_PORT"))
    DB_HOST = environ.get("POSTGRES_HOST")
    DB_URL = environ.get("DB_URL")
    JWT_SECRET: str = environ.get("SECRET_KEY")
    JWT_ALGORITHM: str = environ.get("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRY_TIME = environ.get("ACCESS_TOKEN_EXPIRY_TIME")
    REFRESH_TOKEN_EXPIRY_TIME = environ.get("REFRESH_TOKEN_EXPIRY_TIME")
    PASSWORD_HASHER = CryptContext(schemes=["bcrypt"], deprecated="auto")
    ENVIRONMENT=environ.get("ENVIRONMENT")   

    # Azure OpenAI GPT-4o
    AZURE_OPENAI_GPT_4O_ENDPOINT = environ.get("AZURE_OPENAI_GPT_4O_ENDPOINT")
    AZURE_OPENAI_GPT_4O_API_KEY = environ.get("AZURE_OPENAI_GPT_4O_API_KEY")
    AZURE_OPENAI_GPT_4O_DEPLOYMENT_NAME = environ.get("AZURE_OPENAI_GPT_4O_DEPLOYMENT_NAME")
    AZURE_OPENAI_GPT_4O_MODEL_NAME = environ.get("AZURE_OPENAI_GPT_4O_MODEL_NAME")
    AZURE_OPENAI_GPT_4O_API_VERSION = environ.get("AZURE_OPENAI_GPT_4O_API_VERSION")

settings = Settings()

