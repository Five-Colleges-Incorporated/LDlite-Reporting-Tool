from pathlib import Path

class ScriptFiles:
    def __init__(self, scripts_directory: str):
        self.scripts_directory = Path(scripts_directory)

    def list_script_files(self) -> list[str]:
        files = [x.name for x in sorted(self.scripts_directory.glob('*.sql'))]
        return files

    def read_script_file(self, script_name: str) -> str:
        scriptPath = self.scripts_directory / script_name
        try: 
            script = scriptPath.read_text()
        except FileNotFoundError as err: 
            raise FileNotFoundError(f"Query File: {script_name} not found") from err
        return script
    
    