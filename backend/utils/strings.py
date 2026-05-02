import re


def sanitise(content: str) -> str:
    return re.sub('<[^<]+?>', '', str(content)) if content is not None else ''