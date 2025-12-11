from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session


class DatabaseConnector:
    """SQLAlchemy database wrapper for managing connections and sessions."""

    def __init__(self, connection_string: str):
        """
        Initialize database connection.

        Args:
            connection_string: Database connection URL
                              (e.g., 'mysql://user:pass@host:port/db')
        """
        self.connection_string = connection_string
        self.engine: Optional[Engine] = None
        self._session_maker: Optional[sessionmaker] = None
        self._session: Optional[Session] = None
        self._initialize()

    def _initialize(self) -> None:
        """Create engine and session maker."""
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,
        )
        self._session_maker = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """
        Get database session.

        Returns:
            SQLAlchemy Session instance
        """
        if self._session is None:
            self._session = self._session_maker()
        return self._session

    def close(self) -> None:
        """Close session and dispose engine."""
        if self._session:
            self._session.close()
            self._session = None

        if self.engine:
            self.engine.dispose()
            self.engine = None

        self._session_maker = None
