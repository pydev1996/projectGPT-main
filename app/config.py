from typing import ClassVar
from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES: ClassVar[int]= 60 * 24 * 2  # 2 days
    REFRESH_TOKEN_EXPIRE_MINUTES: ClassVar[int] = 60 * 24 * 15 # 7 days
    ALGORITHM: ClassVar[str] = "HS256"
    JWT_SECRET_KEY: ClassVar[str] = os.environ['JWT_SECRET_KEY']     # should be kept secret
    JWT_REFRESH_SECRET_KEY: ClassVar[str] = os.environ['JWT_REFRESH_SECRET_KEY']      # should be kept secret
    MONGO_DB_URL: ClassVar[str] = os.environ['MONGO_DB_URL']
    DATABASE_NAME: ClassVar[str] = os.environ['DATABASE_NAME']
    MAX_POOL_SIZE: ClassVar[str] = os.environ['MAX_POOL_SIZE']
    OPEN_AI_API_KEY: ClassVar[str] = os.environ["OPEN_AI_API_KEY"]
    PROJECT_ASSISTANT_ID: ClassVar[str] = os.environ["PROJECT_ASSISTANT_ID"]
    EXTRACTSKILLS_ASSISTANT_ID: ClassVar[str] = os.environ["EXTRACTSKILLS_ASSISTANT_ID"]
    MAIL_USERNAME: ClassVar[str] = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD: ClassVar[str] = os.getenv('MAIL_PASSWORD')
    MAIL_FROM: ClassVar[str] = os.getenv('MAIL_FROM')
    MAIL_PORT: ClassVar[str] = int(os.getenv('MAIL_PORT'))
    MAIL_SERVER: ClassVar[str] = os.getenv('MAIL_SERVER')
    MAIL_FROM_NAME: ClassVar[str] = os.getenv('MAIN_FROM_NAME')
    AWS_ACCESS_KEY_ID: ClassVar[str] = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY: ClassVar[str] = os.getenv('AWS_SECRET_ACCESS_KEY')
    FILE_BUCKET_NAME: ClassVar[str] = os.getenv('FILE_BUCKET_NAME')
    
settings = Settings()

