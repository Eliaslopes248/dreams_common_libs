"""Build a Flask app from a database, repository classes, blueprints, and allowed origins."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, Flask
from flask_cors import CORS

from dreams_common.flask_servers.repository import Repository, RepositoryContainer
from dreams_common.logging.logger import GetLogger
from dreams_common.return_code.rc import RC

if TYPE_CHECKING:
    from dreams_common.database.database_service import DatabaseService

logger = GetLogger(__name__)


def AddRepositories(
    server: Flask, database: DatabaseService, repository_map: dict[str, type[Repository]]
) -> RC:
    """Build a repository container using the shared database."""
    try:
        server.repos = RepositoryContainer(database, repository_map)
        return RC.OK
    except Exception:
        logger.exception("Unable to add repositories.")
        return RC.ERROR


def AddRouteBlueprints(server: Flask, blueprint_list: list[Blueprint]) -> RC:
    """Register each blueprint using its configured routes and URL prefix."""
    try:
        for blueprint in blueprint_list:
            server.register_blueprint(blueprint)
        return RC.OK
    except Exception:
        logger.exception("Unable to register route blueprints.")
        return RC.ERROR


def AddCORSAllowList(server: Flask, cors_allowlist: list[str] | None = None) -> RC:
    """Enable CORS for the supplied origins; an empty list allows none."""
    try:
        CORS(server, origins=cors_allowlist or [])
        return RC.OK
    except Exception:
        logger.exception("Unable to configure CORS.")
        return RC.ERROR


def CreateFlaskApp(
    database: DatabaseService,
    repository_map: dict[str, type[Repository]],
    blueprint_list: list[Blueprint],
    cors_allowlist: list[str] | None = None,
    server_name: str = __name__,
) -> tuple[Flask | None, RC]:
    """Create and configure an app; return (None, RC.ERROR) if setup fails."""
    try:
        # Create app instance
        app = Flask(server_name)
        rc = AddRepositories(app, database, repository_map)
        if rc != RC.OK:
            return None, rc

        for configure, value in (
            (AddRouteBlueprints, blueprint_list),
            (AddCORSAllowList, cors_allowlist),
        ):
            rc = configure(app, value)
            if rc != RC.OK:
                return None, rc
        return app, RC.OK
    except Exception:
        logger.exception("Unable to create Flask server.")
        return None, RC.ERROR
