import re
from enum import StrEnum
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class ParameterType(StrEnum):
    Text = "TEXT"
    Date = "DATE"
    File = "SINGLE_COLUMN_CSV_NO_HEADER"
    Dropdown = "DROPDOWN"

@dataclass
class ParameterDefinition:
    arg_name: str
    index: int
    defined_type: ParameterType
    description: str
    required: bool = True
    
    selectable_values: set[str] | None = None
    default: any = None

    def __lt__(self, val):
        return self.index < val.index

@dataclass
class ParameterValue:
    index: int
    description: str
    value: any

    def __lt__(self, val):
        return self.index < val.index

@dataclass
class ParameterValidationError:
    message: str
    index: int

def get_parameters(script_text: str) -> list[ParameterDefinition]:
    rawParamList = re.findall('\%\(.*?\)s', script_text)
    parsedParams = []
    for i, param_string in enumerate(rawParamList):
        paramString = param_string[2:-2]
        paramSplit = paramString.split("__")
        index = i
        defined_type = ParameterType
        selectable_values = None
        default = None
        if paramSplit[1] == "TEXT":
            defined_type = ParameterType.Text
            if len(paramSplit) == 3:
                default = paramSplit[2]
        elif paramSplit[1] == "DATE":
            defined_type = ParameterType.Date
            if len(paramSplit) == 3:
                default = paramSplit[2]
        elif paramSplit[1] == "SINGLE_COLUMN_CSV_NO_HEADER":
            defined_type = ParameterType.File
        elif paramSplit[1] == "DROPDOWN":
            defined_type = ParameterType.Dropdown
            selectable_values = paramSplit[2:]
            default = paramSplit[2]
        else:
            raise ValueError(f"Unknown parameter type {paramSplit[1]}.")
        description = paramSplit[0]
        parsedParams.append(ParameterDefinition(arg_name=paramString, index=index, defined_type=defined_type, 
                                                description=description, selectable_values=selectable_values, default=default))
    return parsedParams

def validate_parameters(script_text: str, parameters: list[ParameterValue]) -> list[ParameterValidationError]:
    parameterDefList = get_parameters(script_text)
    validation = []
    for parameter in parameters:
        parameterDef = [i for i in parameterDefList if i.index == parameter.index]
        if len(parameterDef) > 1:
            validation.append(ParameterValidationError(message="Duplicate index",index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.Date:
            try:
                if parameter.value != datetime.strptime(parameter.value, "%Y-%m-%d"):
                    continue
                else:
                    validation.append(ParameterValidationError(message="Invalid Date", index=parameter.index))
            except:
                validation.append(ParameterValidationError(message="Invalid Date", index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.Dropdown:
            if parameter.value in parameterDef[0].selectable_values:
                continue
            else:
                validation.append(ParameterValidationError(message="Invalid option", index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.File:
            paramPath = Path(parameter.value)
            if paramPath.exists():
                continue
            else:
                validation.append(ParameterValidationError(message="File not found", index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.Text:
            if isinstance(parameter.value, str):
                if parameter.value != '':
                    continue
                else:
                    validation.append(ParameterValidationError(message="Parameter must not be empty", index=parameter.index))
            else:
                validation.append(ParameterValidationError(message="Parameter value must be a string", index=parameter.index))
    return validation
    
def prepare_sql(script_text: str, parameters: list[ParameterValue]) -> tuple[str, tuple[any, ...]]:
    sortedParameters = sorted(parameters, key=lambda parameter: parameter.index)
    return (script_text, tuple(sortedParameters))
