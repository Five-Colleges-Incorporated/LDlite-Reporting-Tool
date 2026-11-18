"""Module for extracting and validating parameters from SQL scripts."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class ParameterType(StrEnum):
    """Enumerated constants for supported parameter types."""

    Text = "TEXT"
    Date = "DATE"
    File = "SINGLE_COLUMN_CSV_NO_HEADER"
    Dropdown = "DROPDOWN"


@dataclass
class ParameterDefinition:
    """Dataclass containing the values which define a query parameter.

    Attributes:
    ----------
    arg_name : str
        The full text of the parameter as it appears in the script.
    index : int
        The position of the parameter in the script.
    defined_type : ParameterType
        The type of parameter.
    description : str
        The name/description to be displayed to users.
    required : bool
        Indicates if the parameter is required. True by default.
    selectable_values : list[str]
        List of possible values for dropdown parameters. None for other parameter types.
    default : any
        Default value to be assigned to the field.

    Methods:
    -------
    __lt__(val: ParameterDefinition) -> bool
        Less than comparison method for ordering parameter definitions.
    """

    arg_name: str
    index: int
    defined_type: ParameterType
    description: str
    selectable_values: list[str]
    required: bool = True
    default: str | None = ""

    def __lt__(self, val) -> bool:
        return self.index < val.index


@dataclass
class ParameterValue:
    """Dataclass for parameter values.

    Attributes:
    ----------
    index : int
        The position of the parameter in the script.
    description : str
        The name/description of the parameter to be displayed to users.
    value : any
        The value to be used for the specified parameter.

    Methods:
    -------
    __lt__(val: ParameterValue) -> bool
        Less than comparison method for ordering parameter values.
    """

    index: int
    description: str
    value: str

    def __lt__(self, val) -> bool:
        return self.index < val.index


@dataclass
class ParameterValidationError:
    """Dataclass for parameter validation error messages.

    Attributes:
    ----------
    message : str
        The message describing the validation error.
    index : int
        The position of the parameter in the script.
    """

    message: str
    index: int


def get_parameters(script_text: str) -> list[ParameterDefinition]:
    """Extract a list of parameter definitions from a script's text.

    Args:
        script_text (str): The SQL script to extract parameters from.
    """
    raw_param_list = re.findall(r"\%\(.*?\)s", script_text)
    parsed_params = []
    for i, raw_param in enumerate(raw_param_list):
        param_string = raw_param[2:-2]
        param_split = param_string.split("__")
        index = i
        defined_type = ParameterType
        default_index = 2
        selectable_values = None
        default = ""
        if param_split[1] == "TEXT":
            defined_type = ParameterType.Text
            if len(param_split) > default_index:
                default = param_split[default_index]
        elif param_split[1] == "DATE":
            default = None
            defined_type = ParameterType.Date
            if len(param_split) > default_index:
                default = param_split[default_index]
        elif param_split[1] == "SINGLE_COLUMN_CSV_NO_HEADER":
            defined_type = ParameterType.File
        elif param_split[1] == "DROPDOWN":
            defined_type = ParameterType.Dropdown
            selectable_values = param_split[default_index:]
            if len(param_split) <= default_index:
                msg = (f"Dropdown parameter '{param_split[0]}'"
                       "must have at least one selectable value.")
                raise ValueError(msg)
            default = param_split[default_index]
        else:
            msg = f"Unknown parameter type {param_split[1]}."
            raise ValueError(msg)
        description = param_split[0]
        parsed_params.append(
            ParameterDefinition(
                arg_name=param_string,
                index=index,
                defined_type=defined_type,
                description=description,
                selectable_values=selectable_values,
                default=default,
            )
        )
    return parsed_params


def validate_parameters(
    script_text: str, parameters: list[ParameterValue]
) -> list[ParameterValidationError]:
    """Validate parameter values against the parameters extracted from a script.

    Args:
        script_text (str) : The SQL script to validate against.
        parameters (list[ParameterValue]) : The list of parameter values to validate.
    """
    parameter_def_list = get_parameters(script_text)

    validation = []
    indexes = []
    for parameter in parameters:
        parameter_def = [i for i in parameter_def_list if i.index == parameter.index]
        if len(parameter_def) == 0:
            validation.append(
                ParameterValidationError(
                    message=f"No parameter found with index {parameter.index}",
                    index=parameter.index,
                )
            )
        elif parameter.index in indexes:
            validation.append(
                ParameterValidationError(
                    message=f"Duplicate parameter with index {parameter.index}",
                    index=parameter.index,
                )
            )
        elif len(parameter_def) > 1:
            validation.append(
                ParameterValidationError(
                    message="Duplicate index", index=parameter.index
                )
            )
        elif parameter_def[0].defined_type == ParameterType.Date:
            try:
                if parameter.value != datetime.strptime(parameter.value, "%Y-%m-%d"):
                    indexes.append(parameter.index)
                    continue
                validation.append(
                    ParameterValidationError(
                        message="Invalid Date", index=parameter.index
                    )
                )
            except ValueError:
                validation.append(
                    ParameterValidationError(
                        message="Invalid Date", index=parameter.index
                    )
                )
        elif parameter_def[0].defined_type == ParameterType.Dropdown:
            if parameter.value in parameter_def[0].selectable_values:
                indexes.append(parameter.index)
                continue
            validation.append(
                ParameterValidationError(
                    message="Invalid option", index=parameter.index
                )
            )
        elif parameter_def[0].defined_type == ParameterType.File:
            param_path = Path(parameter.value)
            if param_path.exists():
                indexes.append(parameter.index)
                continue
            validation.append(
                ParameterValidationError(
                    message="File not found", index=parameter.index
                )
            )
        elif parameter_def[0].defined_type == ParameterType.Text:
            if isinstance(parameter.value, str):
                if parameter.value != "":
                    indexes.append(parameter.index)
                    continue
                validation.append(
                    ParameterValidationError(
                        message="Parameter must not be empty", index=parameter.index
                    )
                )
            else:
                validation.append(
                    ParameterValidationError(
                        message="Parameter value must be a string",
                        index=parameter.index,
                    )
                )
        indexes.append(parameter.index)
    return validation


def prepare_sql(
    script_text: str,
    param_vals: list[ParameterValue],
    param_defs: list[ParameterDefinition],
) -> tuple[list[str], dict]:
    """Returns a list of SQL commands and a dict mapping parameters to their values.

    Args:
        script_text (str): The SQL script to be split into a list of commands.
        param_vals (list[ParameterValue]): Values for the script's parameters.
        param_defs (list[ParameterDefinition]): Definitions for the script's parameters.
    """
    param_dict = {}
    for param_val in param_vals:
        if param_defs[param_val.index].defined_type == ParameterType.File:
            with open(file=param_val.value, encoding="UTF-8") as filereader:
                lines = [x.strip() for x in filereader]
            param_dict[param_defs[param_val.index].arg_name] = lines
        else:
            param_dict[param_defs[param_val.index].arg_name] = param_val.value

    commands = [x.strip() for x in script_text.split(";") if x.strip()]

    return commands, param_dict
