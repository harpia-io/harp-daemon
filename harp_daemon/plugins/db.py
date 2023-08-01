from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from harp_daemon.settings import DbConfig
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

engine = create_engine(f"mariadb+mariadbconnector://{DbConfig.DATABASE_USER}:{DbConfig.DATABASE_PSWD}@{DbConfig.DATABASE_SERVER}:{DbConfig.DATABASE_PORT}/{DbConfig.DATABASE_SCHEMA}")
SQLAlchemyInstrumentor().instrument(
    engine=engine,
)
Session = sessionmaker(bind=engine)

Base = declarative_base()
