from dataclasses import dataclass
from typing import List

@dataclass
class Category:
    name: str
    words: List[str]