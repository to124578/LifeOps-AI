from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import get_settings

Base = declarative_base()
_engine = None
_Session = None


def get_engine():
    global _engine, _Session
    if _engine is None:
        url = get_settings().database_url
        kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
        _engine = create_engine(url, **kwargs)
        _Session = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def SessionLocal():
    get_engine()
    return _Session()


def init_db():
    from ..models import db_models  # noqa: F401  (register tables)

    Base.metadata.create_all(get_engine())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
