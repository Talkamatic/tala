from pathlib import Path


def ddd_files(path):
    patterns = ["*.xml", "*.txt", "*.py", "*.pgf", "*.json"]
    for pattern in patterns:
        for file in Path(path).rglob(pattern):
            yield file
