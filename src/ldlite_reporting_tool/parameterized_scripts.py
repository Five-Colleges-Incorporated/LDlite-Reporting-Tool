import re
from enum import StrEnum
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv


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
    indexes = []
    for parameter in parameters:
        parameterDef = [i for i in parameterDefList if i.index == parameter.index]
        if len(parameterDef) == 0:
            validation.append(ParameterValidationError(message=f"No parameter found with index {parameter.index}", index=parameter.index))
        elif parameter.index in indexes:
            validation.append(ParameterValidationError(message=f"Duplicate parameter with index {parameter.index}", index=parameter.index))
        elif len(parameterDef) > 1: #TODO - What if len(parameterDef) == 0
            validation.append(ParameterValidationError(message="Duplicate index",index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.Date:
            try:
                if parameter.value != datetime.strptime(parameter.value, "%Y-%m-%d"):
                    indexes.append(parameter.index)
                    continue
                else:
                    validation.append(ParameterValidationError(message="Invalid Date", index=parameter.index))
            except:
                validation.append(ParameterValidationError(message="Invalid Date", index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.Dropdown:
            if parameter.value in parameterDef[0].selectable_values:
                indexes.append(parameter.index)
                continue
            else:
                validation.append(ParameterValidationError(message="Invalid option", index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.File:
            paramPath = Path(parameter.value)
            if paramPath.exists():
                indexes.append(parameter.index)
                continue
            else:
                validation.append(ParameterValidationError(message="File not found", index=parameter.index))
        elif parameterDef[0].defined_type == ParameterType.Text:
            if isinstance(parameter.value, str):
                if parameter.value != '':
                    indexes.append(parameter.index)
                    continue
                else:
                    validation.append(ParameterValidationError(message="Parameter must not be empty", index=parameter.index))
            else:
                validation.append(ParameterValidationError(message="Parameter value must be a string", index=parameter.index))
        indexes.append(parameter.index)
    return validation
    
def prepare_sql(script_text: str, param_vals: list[ParameterValue], param_defs: list[ParameterDefinition]) -> tuple[list[str], dict]:
    paramDict = {}
    for param_val in param_vals:
        if param_defs[param_val.index].defined_type == ParameterType.File:
            file = open(param_val.value, 'r')
            filereader = csv.reader(file)
            try:
                lines = []
                for line in filereader:
                        lines.append(line[0].strip())
            except Exception as e:
                raise e
            paramDict[param_defs[param_val.index].arg_name] = lines
        else:
            paramDict[param_defs[param_val.index].arg_name] = param_val.value

    commands = [x.strip() for x in script_text.split(';') if x.strip()]

    return commands, paramDict


if __name__ == "__main__":
    script = "Param1: %(param1__TEXT__Default)s Param2: %(param2__DATE__2026-05-23)s"
    value1 = ParameterValue(3,"param1", "AAARR")
    value2 = ParameterValue(0, "param2", "2025-02-04")
    value3 = ParameterValue(0, "param2", "2025-02-04")

    print(validate_parameters(script_text=script, parameters = [value1,value2,value3]))