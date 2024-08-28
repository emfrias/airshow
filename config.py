from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import os

import logging


def get_database_url():
    db_type = os.getenv('DB_TYPE', 'postgresql')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'postgres')
    host = os.getenv('DB_HOST', 'db')
    port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'adsb')

    if db_type == 'postgresql':
        return f'postgresql://{user}:{password}@{host}:{port}/{db_name}'
    elif db_type == 'mysql':
        return f'mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}'
    elif db_type == 'sqlite':
        return f'sqlite:///{db_name}.db'
    else:
        raise ValueError("Unsupported database type")

engine = create_engine(get_database_url())
Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(bind=engine))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("airshow")

