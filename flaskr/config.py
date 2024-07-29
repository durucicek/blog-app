import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #SQLALCHEMY_ECHO = True
    SECRET_KEY = "dev" 
    JWT_SECRET_KEY = "super-secret" 
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_COOKIE_CSRF_PROTECT = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DEVELOPMENT_DATABASE_URL")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL")

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("STAGING_DATABASE_URL")

config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "staging": StagingConfig
}
