from sqlalchemy.engine.url import URL
import os

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
POSTGRES_DB = {'drivername': 'postgresql',
               'username': os.getenv('db_user', ""),
               'password': os.getenv('db_pass', ""),
               'host': os.getenv('db_host', ""),
               'port': os.getenv('db_port', ""),
               'database': os.getenv('db_name', "")}

SQLALCHEMY_DATABASE_URI = URL(**POSTGRES_DB)
SQLALCHEMY_TRACK_MODIFICATIONS = False

## Optional Configs
# SQLALCHEMY_ECHO = True
# DB_POOL_SIZE = 20
# DB_MAX_OVERFLOW = 5
# SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": DB_POOL_SIZE,
#                             "max_overflow" : DB_MAX_OVERFLOW}
