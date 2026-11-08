"""Ports used by the import use case."""

from typing import Protocol
from .model import ImportCommand, ImportResult


class ImportRepository(Protocol):
    def import_data(self, command: ImportCommand) -> ImportResult: ...
