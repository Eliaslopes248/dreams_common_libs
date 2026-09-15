from __future__ import annotations

from typing import TYPE_CHECKING

from dreams_common.logging.logger import GetLogger

if TYPE_CHECKING:
    from dreams_common.database.database_service import DatabaseService

logger = GetLogger(__name__)

class Repository:
    db: DatabaseService
    def __init__(self, database: DatabaseService):
        self.db = database


class RepositoryContainer:
    """This class will contain all repositories for the server."""

    db: DatabaseService

    def __init__(self, database: DatabaseService, repo_map: dict[str, type[Repository]]):
        self.db = database
        # Add object fields to object
        for repo_name, repo_class in repo_map.items():
            
            # Inject database
            repo = repo_class(database)

            # Add field
            self.__setattr__(repo_name, repo)
        logger.info(f"Repositories have been loaded into RepositoryContainer.")
