import psycopg as postgres
from contextlib import contextmanager
import logging
from parameterized_scripts import ParameterDefinition, ParameterValue, prepare_sql


class PostgresDB:
    def __init__(self, dbname: str, user: str, password: str, host:str, port: str): 
        self._conn = postgres.connect(f'dbname={dbname} user={user} password={password} host={host} port={port}')
    
    @contextmanager
    def stream_query(self, script: str, param_vals: list[ParameterValue], param_defs: list[ParameterDefinition]) -> memoryview:
        commands, param_dict = prepare_sql(script_text=script, param_vals=param_vals, param_defs=param_defs)

        logging.info("Script broken into %s commands", len(commands))

        if len(commands) > 1:
            logging.info("Executing setup commands")
            with postgres.ClientCursor(self._conn) as cur:
                for command in commands[:-1]:
                    cur.execute(query=command, params=param_dict)
        logging.info("Setup commands executed successfully")
        
        logging.info("Streaming results of query command")
        command = commands[-1].strip(";").strip()

        with postgres.ClientCursor(self._conn) as cur, cur.copy(f"COPY ({command}) TO STDOUT WITH (FORMAT CSV, HEADER, DELIMITER '\t');", param_dict) as results:
            yield results