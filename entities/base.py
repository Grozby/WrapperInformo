# coding=utf-8
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# TODO insert correct mysql credentials
engine = create_engine('mysql+pymysql://wrapper:b0ss@localhost:3306/wrapper_informo')
Session = sessionmaker(bind=engine)

Base = declarative_base()
