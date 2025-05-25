from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from skylock.config import DATABASE_URL


def get_db_session():
    """Provides a SQLAlchemy database session as a context manager.

    This function creates a database engine and session factory. It yields
    a session, attempts to commit transactions upon successful completion
    of the `with` block, and rolls back the transaction in case of
    a SQLAlchemyError.

    Yields:
        sqlalchemy.orm.Session: A database session object.

    Raises:
        SQLAlchemyError: If an error occurs during database operations,
                         the transaction is rolled back and the error is re-raised.
    """
    engine = create_engine(DATABASE_URL)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        try:
            yield session
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
