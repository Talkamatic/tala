import os

from pathlib import Path


class UTF8FileWriter(object):
    def __init__(self, path):
        super(UTF8FileWriter, self).__init__()
        self._path = path if isinstance(path, Path) else Path(path)

    def create_directories(self):
        if not self._path.parent.exists():
            os.makedirs(str(self._path.parent))

    def write(self, data):
        with self._path.open("w", encoding="utf-8") as file_:
            file_.write(unicode(data))
