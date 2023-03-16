import enum


class LogFormat(str, enum.Enum):
    PLAIN_TEXT = "PLAIN_TEXT"
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"
