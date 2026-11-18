"""An adapter for listing and reading SQL script files."""

from pathlib import Path


class ScriptFiles:
    """Lists and reads SQL script files.

    Attributes:
    ----------
    scripts_directory : Path
        Path to the directory containing SQL scripts.

    Methods:
    -------
    list_script_files() -> list[str]
        Returns a list of script file names from the scripts directory.
    read_script_file(script_name: str) -> str
        Reads and returns the text of a specified query file.
    """

    def __init__(self, scripts_directory: str):
        """Initialize the script file reader.

        Args:
            scripts_directory (str): Path to the directory containing SQL scripts.
        """
        self.scripts_directory = Path(scripts_directory)

    def list_script_files(self) -> list[str]:
        """Returns a list of script file names from the scripts directory."""
        return [x.name for x in sorted(self.scripts_directory.glob("*.sql"))]

    def read_script_file(self, script_name: str) -> str:
        """Returns the text of a specified script file.

        Args:
            script_name (str): Name of the script file to be read.
        """
        script_path = self.scripts_directory / script_name
        try:
            script = script_path.read_text()
        except FileNotFoundError as err:
            msg = f"Query File: {script_name} not found"
            raise FileNotFoundError(msg) from err
        return script
