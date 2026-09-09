from abc import ABC, abstractmethod
from pathlib import Path

class OutputFile:
    def __init__(self, out_file_name: str, out_file_directory: str): 
        self.out_file_name = Path(out_file_directory) / out_file_name

    @abstractmethod
    def write(self, rows: memoryview) -> None: 
        pass

class LocalOutputFile(OutputFile): 
    def write(self, rows:memoryview) -> None:
        with open(self.out_file_name, 'wb') as outfile:
            for row in rows:
                outfile.write(row)
