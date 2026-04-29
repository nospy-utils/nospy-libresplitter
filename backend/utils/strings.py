import re


def sanitise(content: str) -> str:
    return re.sub('<[^<]+?>', '', content) if content is not None else ''