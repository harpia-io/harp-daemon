from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from harp_daemon.settings import DbConfig

engine = create_engine(f"mariadb+mariadbconnector://{DbConfig.DATABASE_USER}:{DbConfig.DATABASE_PSWD}@{DbConfig.DATABASE_SERVER}:{DbConfig.DATABASE_PORT}/{DbConfig.DATABASE_SCHEMA}")
Session = sessionmaker(bind=engine)

Base = declarative_base()
