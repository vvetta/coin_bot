"""Настройка базы данных. DB settings."""

DATABASE_URL: str = "sqlite+aiosqlite:///./db.sqlite3"
DATABASE_ECHO: bool = False


"""Настройка частоты запроса к API"""

MARKET_UPDATE_TIME_SECONDS: int = 3600
