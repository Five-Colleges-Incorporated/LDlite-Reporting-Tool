"""Handlers for user actions."""

from .adapters.output_file import OutputFile
from .adapters.postgres import PostgresDB
from .adapters.script_files import ScriptFiles
from .parameterized_scripts import (
    ParameterDefinition,
    ParameterValue,
    get_parameters,
    validate_parameters,
)


class Handlers:
    """Handlers for various user actions.

    Attributes:
    ----------
    output_file_creator : OutputFile
        Adapter for writing output files.
    script_files : ScriptFiles
        Adapter to list and read SQL scripts.
    db : PostgresDB
        Adapter to connect to and execute queries against a PostgreSQL database.

    Methods:
    -------
    handle_page_load() -> list[str]
        Returns the list of SQL script file names.
    handle_script_selected(script_name: str) -> list[ParameterDefinition]
        Reads selected script and returns its list of parameter definitions.
    handle_script_submitted(outfile_name: str, script_name: str,
    values: list[ParameterValue]) -> list[ValueError]
        Executes a selected script with the specified
        parameter values and saves the output.
    """

    def __init__(
        self, output_file_creator: OutputFile, script_files: ScriptFiles, db: PostgresDB
    ):
        """Initialize the handlers.

        Args:
            output_file_creator (OutputFile): Adapter for handling data output.
            script_files (Scriptfiles): Adapter for listing and reading SQL script files
            db (PostgresDB): Adapter for executing SQL scripts
        """
        self.output_file_creator = output_file_creator
        self.script_files = script_files
        self.db = db

    def handle_page_load(self) -> list[str]:
        """Returns the list of SQL script file names."""
        return self.script_files.list_script_files()

    def handle_script_selected(self, script_name: str) -> list[ParameterDefinition]:
        """Reads selected script and returns its list of parameter definitions.

        Args:
            script_name (str): Name of the selected SQL script file.
        """
        selected_script_text = self.script_files.read_script_file(
            script_name=script_name
        )
        return get_parameters(selected_script_text)

    def handle_script_submitted(
        self, outfile_name: str, script_name: str, values: list[ParameterValue]
    ) -> list[ValueError]:
        """Executes script with the supplied parameter values and saves the output.

        Args:
            outfile_name (str): Name of the output file.
            script_name (str): Name of the selected SQL script file.
            values (list[ParameterValue]): List of the parameter values.
        """
        script_text = self.script_files.read_script_file(script_name=script_name)
        param_definitions = get_parameters(script_text=script_text)

        # Validate parameter values
        validation_results = validate_parameters(
            script_text=script_text, parameters=values
        )
        if len(validation_results) > 0:
            validation_errors = []
            for validation in validation_results:
                validation_errors.extend(
                    [
                        param
                        for param in param_definitions
                        if param.index == validation.index
                    ]
                )
            return validation_errors

        # Execute commands and write output file
        with self.db.stream_query(
            script=script_text, param_vals=values, param_defs=param_definitions
        ) as results:
            self.output_file_creator.write(out_file_name=outfile_name, rows=results)
        return []
