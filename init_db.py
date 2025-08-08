from app.database import init_db, engine, Base
from app.models import user, task
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()