# # # # # # # # # # # # # # USAGE # # # # # # # # # # # # # # #
#
#
# FIRST RUN creates the function in the database and assigns
# the function-triggers to all the models with an updated_at
# property on them.
#
#     python scripts/updated_at_trigger.py
#
#
#
# SUBSEQUENT RUNS take in a single table name and only create
# the function-trigger for that table
#
#     python scripts/updated_at_trigger.py <tablename>
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


import asyncio
import sys

from p3orm import Porm, Table

from ehp.db import models
from ehp.settings import Settings
from ehp.utils.log import get_logger, log_exception

logger = get_logger(__name__)

FUNCTION_SQL = """
CREATE  FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';
"""

TRIGGER_SQL = """
CREATE TRIGGER update_updated_at 
	BEFORE UPDATE ON "{table_name}"
	FOR EACH ROW EXECUTE PROCEDURE update_updated_at();
"""


async def run(tablename: str | None = None):

    await Porm.connect(dsn=Settings.DATABASE_URL)

    if not tablename:
        try:
            await Porm.connection.execute(FUNCTION_SQL)
            logger.info("Created update_updated_at function!")
        except Exception as e:
            log_exception(logger.exception, "couldnt create update_updated_at function", e)

    for obj_name in dir(models):
        obj = getattr(models, obj_name)

        if hasattr(obj, "__tablename__") and hasattr(obj, "updated_at"):
            obj: Table
            logger.info(f"checking {obj.__tablename__=}")

            if tablename:
                if obj.__tablename__ == tablename:
                    try:
                        await Porm.connection.execute(TRIGGER_SQL.format(table_name=obj.__tablename__))
                        logger.info(f"Created trigger for {obj.__tablename__}")
                    except Exception as e:
                        log_exception(logger.exception, f"couldnt create trigger for {obj.__tablename__}", e)

            else:
                try:
                    await Porm.connection.execute(TRIGGER_SQL.format(table_name=obj.__tablename__))
                    logger.info(f"Created trigger for {obj.__tablename__}")
                except Exception as e:
                    log_exception(logger.exception, f"couldnt create trigger for {obj.__tablename__}", e)

    await Porm.disconnect()


if __name__ == "__main__":

    last_arg: str = sys.argv[-1]

    tablename = None if last_arg.endswith(".py") else last_arg

    asyncio.run(run(tablename=tablename))
