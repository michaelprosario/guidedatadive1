from .model import ImportCommand, ImportResult
from .ports import ImportRepository


class ImportGuide:
    def __init__(self, repository: ImportRepository):
        self.repository = repository

    def execute(self, command: ImportCommand) -> ImportResult:
        return self.repository.import_data(command)
