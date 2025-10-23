from sqlalchemy import create_engine
from app.config import get_settings

def get_engine():
    """
    Crea un motor SQLAlchemy con pre_ping para conexiones robustas.
    """
    s = get_settings()
    uri = (
        f"mysql+pymysql://{s.DB_USER}:{s.DB_PASSWORD}"
        f"@{s.DB_HOST}:{s.DB_PORT}/{s.DB_NAME}?charset=utf8mb4"
    )
    return create_engine(uri, pool_pre_ping=True)
