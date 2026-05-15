from dataclasses import dataclass
from enum import Enum


class EntityType(str, Enum):
    PHONE = "PHONE"
    POSTAL = "POSTAL"
    MY_NUMBER = "MY_NUMBER"
    EMAIL = "EMAIL"
    AMOUNT = "AMOUNT"
    IP = "IP"
    LICENSE = "LICENSE"
    CARD = "CARD"
    URL = "URL"
    CONTRACT = "CONTRACT"
    PERSON = "PERSON"
    ORG = "ORG"
    LOCATION = "LOCATION"
    COMPANY_DICT = "COMPANY_DICT"


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    text: str
    entity_type: EntityType
    source: str  # "regex" | "ner" | "dict"

    def __len__(self) -> int:
        return self.end - self.start
