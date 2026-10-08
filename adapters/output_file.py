from abc import ABC, abstractmethod
from pathlib import Path
from collections.abc import Iterator, Buffer

class OutputFile:
    def __init__(self, out_file_directory: str): 
        self.out_file_directory = Path(out_file_directory)

    @abstractmethod
    def write(self, out_file_name: str, rows: memoryview) -> None: 
        pass

class LocalOutputFile(OutputFile): 
    def write(self, out_file_name: str,  rows:memoryview) -> None:
        out_file_path = self.out_file_directory / out_file_name
        with open(out_file_path, 'wb') as outfile:
            for row in rows:
                outfile.write(row)