"""Initial database seeding module."""
import logging
from sqlalchemy.orm import Session
from app.core.seed_rbac import seed_rbac_data

logger = logging.getLogger(__name__)

def seed_initial_data(db: Session):
    """Seed all initial system data into the database."""
    logger.info("Initializing database seeding...")
    seed_rbac_data(db)
    logger.info("Database seeding finished.")
