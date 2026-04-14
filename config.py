# This will handle:
# DB file name and location | secret key (login sessions) | debug settings | security related configs.

import os

class Config:
    # database file name and location
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")

    # secret key for login sessions
    SECRET_KEY = "change_this_secret_key"

    # debug mode
    DEBUG = True