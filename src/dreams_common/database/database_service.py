from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
# add api root to path so imports resolve when run as a script
api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from logging import GetLogger
from return_code import RC

# Check what kind of database is needed
DB_SERVICE_TYPE = os.getenv("DH_DB_SERVICE_TYPE", default="SUPABASE").upper()
logger = GetLogger(__name__)

if DB_SERVICE_TYPE == "MYSQL":
    try:
        import mysql.connector.pooling
        from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection
    except Exception as e:
        logger.error(f"Unable to import required modules for MySQL. {e}")
        sys.exit(1)

elif DB_SERVICE_TYPE in ("SUPABASE", "POSTGRES"):
    try:
        from psycopg_pool import ConnectionPool
    except Exception as e:
        logger.error(f"Unable to import required modules for SUPABASE. {e}")
        sys.exit(1)

else:
    logger.error(f"Unknown DH_DB_SERVICE_TYPE '{DB_SERVICE_TYPE}'. Expected MYSQL, SUPABASE, or POSTGRES.")
    sys.exit(1)



class DatabaseService(ABC):
    """Parent class for all database services. Subclasses must implement every method."""

    def __init__(self) -> None:
        pass

    @abstractmethod
    def HealthCheck(self) -> RC:
        """Check if the database connection is healthy."""
        ...

    @abstractmethod
    def GetConnection(self) -> Any:
        """Return a connection from the pool."""
        ...

    @abstractmethod
    def ExecuteQuery(
        self,
        query: str,
        params: tuple = None,
        expects_return: bool = True,
        commit: bool = True
    ) -> tuple[Any, RC]:
        """Execute a query string against the database."""
        ...

    @abstractmethod
    def ExecuteMany(
        self,
        query: str,
        params: list[tuple],
        commit: bool = True
    ) -> tuple[Any, RC]:
        """Execute a query with multiple sets of parameters."""
        ...

class SupabaseService(DatabaseService):
    """PostgreSQL service implementation for a Supabase-hosted database."""

    pool_size: int
    host: str
    port: int
    user: str
    password: str
    database: str

    pool: ConnectionPool

    def __init__(
        self,
        pool_size: int = 10,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
    ) -> None:
        super().__init__()

        logger.info("Initializing SupabaseService...")
        logger.info("Loading PostgreSQL credentials...")

        self.pool_size = pool_size
        self.host = host or os.getenv("SUPABASE_HOST") or os.getenv("POSTGRES_HOST")
        self.port = (
            port
            if port is not None
            else int(os.getenv("SUPABASE_PORT") or os.getenv("POSTGRES_PORT") or 5432)
        )
        self.user = user or os.getenv("SUPABASE_USER") or os.getenv("POSTGRES_USER")
        self.password = password or os.getenv("SUPABASE_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
        self.database = (
            database
            or os.getenv("SUPABASE_DB")
            or os.getenv("POSTGRES_DB")
            or "postgres"
        )

        # Create connection pool
        # ConnectionPool takes conninfo/kwargs, not host/user as top-level args
        self.pool = ConnectionPool(
            kwargs={
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.password,
                "dbname": self.database,
            },
            min_size=1,
            max_size=self.pool_size,
        )

        logger.info("PostgreSQL connection pool created successfully.")

    def HealthCheck(self) -> RC:
        """This method will check if the connection is healthy."""
        connection = None
        try:
            connection = self.pool.getconn()
            logger.info(f"Connection: {connection}")
            logger.info(f"PostgreSQL server connection is healthy.")
            return RC.OK

        except Exception as e:
            logger.error(f"Unable to establish connection. {e}")
            return RC.DATABASE_ERROR

        finally:
            if connection:
                self.pool.putconn(connection)

    def GetConnection(self) -> Any:
        """This method will return a connection from pool."""
        try:
            connection = self.pool.getconn()
            return connection
        except Exception as e:
            logger.error(f"Unable to get connection from server pool. {e}")
            return None

    def ExecuteQuery(self, query: str, params: tuple = None, expects_return: bool = True, commit: bool = True) -> tuple[Any, RC]:
        """This method will execute a string PostgreSQL query."""

        # Get connection from pool
        connection = self.GetConnection()

        results = None
        cursor = None

        try:
            cursor = connection.cursor()

            # Add params to query if given
            if params is not None:
                if not isinstance(params, tuple):
                    params = tuple(params)

                # Execute commands
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get returned results from server
            if expects_return:
                results = cursor.fetchall()

            # Persist writes; psycopg rolls back on return-to-pool otherwise
            if commit:
                connection.commit()
            logger.info(f"PostgreSQL command executed successfully.")

        except Exception as e:
            logger.error(f"Unable to execute PostgreSQL commands. {e}")
            return None, RC.DATABASE_ERROR
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.pool.putconn(connection)

        return results, RC.OK

    def ExecuteMany(
        self,
        query: str,
        params: list[tuple],
        commit: bool = True,
    ) -> tuple[Any, RC]:
        """Execute a PostgreSQL query with multiple sets of parameters."""

        # Nothing to execute
        if not params:
            return None, RC.OK

        # Get pool connection
        connection = self.GetConnection()
        cursor = None

        try:
            cursor = connection.cursor()

            # Execute query for every parameter tuple
            cursor.executemany(query, params)

            # Commit INSERT / UPDATE / DELETE
            if commit:
                connection.commit()

            logger.info(f"PostgreSQL command executed successfully for {len(params)} rows.")
            affected_rows = cursor.rowcount

            return affected_rows, RC.OK

        except Exception:
            if connection:
                connection.rollback()

            logger.exception("Unable to execute PostgreSQL commands.")

            return None, RC.DATABASE_ERROR

        finally:
            if cursor:
                cursor.close()

            if connection:
                self.pool.putconn(connection)

class MySQLService(DatabaseService):
    """This class is a MySQL service implementation"""

    pool_size:  int # size of connection pool
    pool_name:  int # name of connection pool
    host:       str # mysql server host
    user:       str # mysql server user
    password:   str # mysql server password
    database:   str # mysql database

    pool:       MySQLConnectionPool

    def __init__(
        self, 
        pool_name:  str=None,
        pool_size:  int=10, 
        host:       str=None,
        user:       str=None,
        password:   str=None,
        database:   str="bettafits"
        ) -> None:
        # Execute parent class constructor
        super().__init__()

        logger.info(f"Initializing MySQLClient...")
        logger.info(f"Loading MySQLClient credentials.")

        # Get connection credentials
        self.pool_size  = pool_size
        self.pool_name  = pool_name or "rest_api_pool"
        self.host       = host      or os.getenv("MYSQL_HOST", None)
        self.user       = user      or os.getenv("MYSQL_USER", None)
        self.password   = password  or os.getenv("MYSQL_PASSWORD", None)
        self.database   = database  or "bettafits"

        # Create connection pool
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_size=self.pool_size,
            pool_name=self.pool_name,
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

        logger.info(f"Connection pool created successfully.")
        

    def HealthCheck(self) -> RC:
        """This method will check if the connection is healthy."""
        try:
            connection = self.pool.get_connection()
            logger.info(f"Connection: {connection}")
            logger.info(f"MySQL server connection is healthy.")
            return RC.OK

        except Exception as e:
            logger.error(f"Unable to establish connection. {e}")
            return RC.MYSQL_CONNECTION_ERROR
        
    def GetConnection(self) -> PooledMySQLConnection:
        """This method will return a connection from pool."""
        try:
            connection = self.pool.get_connection()
            return connection
        except Exception as e:
            logger.error(f"Unable to get connection from server pool. {e}")
            return None
    
    def ExecuteQuery(self, query: str, params: tuple = None, expects_return: bool = True, commit: bool = True) -> tuple[Any, RC]:
        """This method will execute a string MySQL query."""
        
        # Get connection from pool
        connection: PooledMySQLConnection  = self.GetConnection()
        
        results = None
        cursor  = None

        try:
            cursor = connection.cursor()

            # Add params to query if given
            if params is not None:
                if not isinstance(params, tuple):
                    params = tuple(params)
                
                # Execute commands
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get returned results from server
            if expects_return:
                results = cursor.fetchall()
            
            if commit:
                connection.commit()
            logger.info(f"MySQL command executed successfully.")
            
        except Exception as e:
            logger.error(f"Unable to execute MySQL commands. {e}")
            return None, RC.MYSQL_SERVER_ERROR
        finally:
            # Close pool connection
            if connection:
                connection.close()
            if cursor:
                cursor.close()
 
        return results, RC.OK

    def ExecuteMany(
        self,
        query: str,
        params: list[tuple],
        commit: bool = True,
    ) -> tuple[Any, RC]:
        """Execute a MySQL query with multiple sets of parameters."""

        # Nothing to execute
        if not params:
            return None, RC.OK

        # Get pool connection
        connection: PooledMySQLConnection = self.GetConnection()
        cursor = None

        try:
            cursor = connection.cursor()

            # Execute query for every parameter tuple
            cursor.executemany(query, params)

            # Commit INSERT / UPDATE / DELETE
            if commit:
                connection.commit()

            logger.info(f"MySQL command executed successfully for {len(params)} rows.")
            affected_rows = cursor.rowcount

            return affected_rows, RC.OK

        except Exception:
            connection.rollback()

            logger.exception("Unable to execute MySQL commands.")

            return None, RC.MYSQL_SERVER_ERROR

        finally:
            # close connection and cursor
            if cursor:
                cursor.close()

            if connection:
                connection.close()


def GetDatabaseService() -> DatabaseService:
    """Return the database service selected by DH_DB_SERVICE_TYPE."""
    if DB_SERVICE_TYPE == "MYSQL":
        return MySQLService()

    if DB_SERVICE_TYPE in ("SUPABASE", "POSTGRES"):
        return SupabaseService()

    raise ValueError(
        f"Unknown DH_DB_SERVICE_TYPE '{DB_SERVICE_TYPE}'. Expected MYSQL, SUPABASE, or POSTGRES."
    )
