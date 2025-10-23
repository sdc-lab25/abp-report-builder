import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    THEME_URL: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    TZ: str = "Europe/Madrid"  # por defecto

def get_settings() -> Settings:
    """
    Lee variables de entorno (si existen) y aplica valores por defecto
    idénticos a los del script original para mantener compatibilidad.
    """
    return Settings(
        THEME_URL=os.getenv("THEME_URL", "https://script.google.com/macros/s/AKfycbxTwFHszdpmLvibmNuvcvNxT4U9tzhawSyZrx6b4zCiFTQm-lfQioxjvD-lCpr5q2QVKg/exec"),
        DB_HOST=os.getenv("DB_HOST", "dpe.cl0glysfjbui.eu-west-1.rds.amazonaws.com"),
        DB_PORT=int(os.getenv("DB_PORT", "3306")),
        DB_NAME=os.getenv("DB_NAME", "db_watford"),
        DB_USER=os.getenv("DB_USER", "admin"),
        DB_PASSWORD=os.getenv("DB_PASSWORD", "dpeQwertyuiop135790_!#"),
        TZ=os.getenv("TZ", "Europe/Madrid"),
    )
