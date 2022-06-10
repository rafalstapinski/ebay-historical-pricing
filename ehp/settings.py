from os import environ


class Settings:
    ENV = environ["ENV"]
    DATABASE_URL = environ["DATABASE_URL"]


class EnvTypes:
    PROD = "prod"
    DEV = "dev"
    TEST = "test"
