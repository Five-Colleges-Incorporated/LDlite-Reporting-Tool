"""An adapter to query against the PostgreSQL database."""

import logging
from contextlib import contextmanager

import psycopg as postgres
from psycopg import Copy
from typing_extensions import Generator

from ldlite_reporting_tool.parameterized_scripts import (
    ParameterDefinition,
    ParameterValue,
    prepare_sql,
)

logger = logging.getLogger(__name__)


class PostgresDB:
    """Connects to and executes queries against the PostgreSQL database.

    Attributes:
    ----------
    _conn : postgres.Connection
        The postgreSQL database connection.

    Methods:
    -------
    stream_query(script: str, param_vals: list[ParameterValue],
    param_defs: list[ParameterDefinition]) -> memoryview
        Executes the supplied query and returns a memoryview buffer with the output.
    """

    def __init__(self, dbname: str, user: str, password: str, host: str, port: str):
        """Initialize the postgres database connection.

        Args:
            dbname (str): The database name.
            user (str): The database authentication username.
            password (str): The database authentication password.
            host (str): The database host URL.
            port (str): The connection port.
        """
        self._conn = postgres.Connection.connect(
            f"dbname={dbname} user={user} password={password} host={host} port={port}"
        )

    @contextmanager
    def stream_query(
        self,
        script: str,
        param_vals: list[ParameterValue],
        param_defs: list[ParameterDefinition],
    ) -> Generator[Copy]:
        """Execute the supplied query and returns a memoryview buffer with the output.

        Args:
            script (str): The query string.
            param_vals (list[ParameterValue]): The user-supplied parameter values.
            param_defs (list[ParameterDefinition]): The query parameter definitions.
        """
        commands, param_dict = prepare_sql(
            script_text=script, param_vals=param_vals, param_defs=param_defs
        )

        logger.info("Script broken into %s commands", len(commands))

        if len(commands) > 1:
            logger.info("Executing setup commands")
            with postgres.ClientCursor(self._conn) as cur:
                for command in commands[:-1]:
                    cur.execute(query=command, params=param_dict)
        logger.info("Setup commands executed successfully")

        logger.info("Streaming results of query command")
        command = commands[-1].strip(";").strip()
        try:
            with (
                postgres.ClientCursor(self._conn) as cur,
                cur.copy(
                    f"""COPY ({command}) TO STDOUT WITH
                        (FORMAT CSV, HEADER, DELIMITER '\t');""",
                    param_dict,
                ) as results,
            ):
                yield results
        finally:
            self._conn.rollback()
