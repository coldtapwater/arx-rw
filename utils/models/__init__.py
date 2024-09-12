from tortoise import Tortoise
import logging

logger = logging.getLogger('bot')

async def init_db(db_user, db_password, db_host, db_port):
    logger.debug(f"Initializing DB with: user={db_user}, host={db_host}, port={db_port}")
    
    db_url = f'postgres://{db_user}:{db_password}@{db_host}:{db_port}/bot_db'
    logger.debug(f"DB URL: {db_url}")

    try:
        await Tortoise.init(
            db_url=db_url,
            modules={'models': ['utils.models.models']}
        )
        logger.debug("Tortoise init completed")

        # Generate schemas
        logger.info("Generating database schemas...")
        await Tortoise.generate_schemas(safe=True)
        logger.info("Database schemas generated successfully")

    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise

    logger.debug("Database initialization completed successfully")