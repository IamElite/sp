from abc import ABC, abstractmethod
from typing import Optional


class BaseMetadataProvider(ABC):
    @abstractmethod
    def search(self, title: str) -> Optional[dict]:
        ...

    @abstractmethod
    def get_details(self, source_id: str) -> Optional[dict]:
        ...
