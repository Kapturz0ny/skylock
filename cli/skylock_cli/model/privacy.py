from enum import Enum

class Privacy(str, Enum):
    PRIVATE = "private"
    PROTECTED = "protected"
    PUBLIC = "public"