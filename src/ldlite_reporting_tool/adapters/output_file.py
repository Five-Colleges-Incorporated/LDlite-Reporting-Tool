"""An adapter for writing output data."""

from abc import abstractmethod
from pathlib import Path

from psycopg import Copy


class OutputFile:
    """Abstract class for handling data output.

    Attributes:
    ----------
    out_file_directory : Path
        The path to the directory where output will be saved.

    Methods:
    -------
    write(out_file_name: str, rows: memoryview) -> None
        The output method to be implemented by subclasses.
    """

    def __init__(self, out_file_directory: str):
        """Initialize the OutFile object, storing the output path.

        Args:
            out_file_directory (str): The output path as a string.
        """
        self.out_file_directory = Path(out_file_directory)

    @abstractmethod
    def write(self, out_file_name: str, rows: Copy) -> None:
        """Output method to be implemented by subclasses."""


class LocalOutputFile(OutputFile):
    """Implementation of OutputFile for saving output locally.

    Attributes:
    ----------
    out_file_directory : Path
        The path to the directory where output will be saved.

    Methods:
    -------
    write(out_file_name: str, rows: memoryview) -> None
        Saves streamed output to a local file.
    """

    def write(self, out_file_name: str, rows: Copy) -> None:
        """Saves streamed output to a local file.

        Args:
        out_file_name (str):
            The name of the output file.
        rows (memoryview):
            The buffer interface to stream query output.
        """
        out_file_path = self.out_file_directory / out_file_name
        with open(out_file_path, "wb") as outfile:
            outfile.writelines(rows)
