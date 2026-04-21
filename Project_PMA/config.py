import os

class Config:
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")
    SECRET_KEY = "change_this_secret_key"
    DEBUG = True
