from adapters.output_file import OutputFile
from adapters.postgres import PostgresDB
from parameterized_scripts import ParameterDefinition, ParameterValue, get_parameters, validate_parameters
from adapters.script_files import ScriptFiles

class Handlers:
    def __init__(self, output_file_creator: OutputFile, script_files: ScriptFiles, db: PostgresDB):
        self.output_file_creator = output_file_creator
        self.script_files = script_files
        self.db = db

    def handle_page_load(self) -> list[str]:
        return self.script_files.list_script_files()
  
    def handle_script_selected(self, script_name: str) -> list[ParameterDefinition]:
        selected_script_text = self.script_files.read_script_file(script_name=script_name)
        return get_parameters(selected_script_text)

    def handle_script_submitted(self, outfile_name: str, script_name: str, values: list[ParameterValue]) -> list[ValueError] | int:
        script_text = self.script_files.read_script_file(script_name=script_name)
        param_definitions = get_parameters(script_text=script_text)

        # Validate parameter values
        validation_results = validate_parameters(script_text=script_text, parameters=values)
        if len(validation_results) > 0:
            validation_errors = []
            for validation in validation_results:
                for param in param_definitions:
                    if validation.index == param.index:
                        validation_errors.append(ValueError(f"{param.description} -- {validation.message}"))
            return validation_errors

        # Execute commands and write output file
        try:
            with self.db.stream_query(script=script_text, param_vals=values, param_defs=param_definitions) as results:
                self.output_file_creator.write(out_file_name=outfile_name, rows=results)
        except Exception as e:
            raise(e)
        finally:
            self.db.rollback()
        return -1
        