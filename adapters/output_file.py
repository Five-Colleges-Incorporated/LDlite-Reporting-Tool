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
<<<<<<< HEAD
    def write(self, rows:Iterator[Buffer]) -> None:
        with open(self.out_file_name, 'wb') as outfile:
=======
    def write(self, out_file_name: str,  rows:memoryview) -> None:
        out_file_path = self.out_file_directory / out_file_name
        with open(out_file_path, 'wb') as outfile:
>>>>>>> 0604eb8 (Create 'handlers' module to handle user interface actions)
            for row in rows:
                outfile.write(row)