from abc import ABC, abstractmethod


class JobSource(ABC):
    @abstractmethod
    def collect(self) -> list[dict]:
        """Return source records without applying eligibility rules."""

