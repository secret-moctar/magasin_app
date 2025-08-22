import os
from sensitives_info import SQLALCHEMY_DATABASE_URI_local


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", SQLALCHEMY_DATABASE_URI_local)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("ny secret key", "dev")

