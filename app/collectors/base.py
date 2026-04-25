from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import IntelItem


class Collector(ABC):
    name: str

    @abstractmethod
    def collect(self) -> list[IntelItem]:
        raise NotImplementedError
