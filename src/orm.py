from enum import Enum as _Enum
from contextlib import contextmanager

from sqlalchemy import Integer, Text, Column, DateTime, Index, Enum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import sessionmaker

DB_POOL = None

HTTP_METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT')

HttpMethods = _Enum('HttpMethods', ' '.join(HTTP_METHODS))

Session = None

Base = declarative_base()

class PyAppLog(Base):
    __tablename__ = 'pyapp_log'

    id = Column(Integer, primary_key=True, nullable=False)
    time = Column(DateTime(timezone=True), nullable=False)
    src_ip = Column(INET, nullable=False)
    src_port = Column(Integer, nullable=False)
    dst_ip = Column(INET, nullable=False)
    dst_port = Column(Integer, nullable=False)
    http_method = Column(Enum(*HTTP_METHODS, name='http_method'), nullable=False)
    http_path = Column(Text, nullable=False)
    http_query = Column(Text, nullable=False)
    user_agent = Column(Text, nullable=False)

    def __init__(self, time, src_ip, src_port, dst_ip, dst_port, http_method, http_path, http_query, user_agent):
        assert http_method in HttpMethods

        self.time = time
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.http_method = http_method.name
        self.http_path = http_path
        self.http_query = http_query
        self.user_agent = user_agent

    @property
    def src(self):
        return '{0}:{1}'.format(self.src_ip, self.src_port)

    @property
    def dst(self):
        return '{0}:{1}'.format(self.dst_ip, self.dst_port)

Index('pyapp_log_time_idx', PyAppLog.__table__.c.time.desc())

def get_engine(SERVICES):
    for k in SERVICES:
        if k.startswith('postgresql'):
            try:
                uri = SERVICES[k][0]['credentials']['uri']
            except (KeyError, IndexError):
                continue
    
            if uri.startswith('postgres://'):
                db_uri = uri.replace('postgres://', 'postgresql+pypostgresql://')
                print('db_uri', db_uri)
                return create_engine(db_uri, echo=True)

def init_database(engine):
    global Session

    Base.metadata.create_all(engine)

    if Session is None:
        Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()

    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    from cf import SERVICES
    
    engine = get_engine(SERVICES)
    init_database(engine)
