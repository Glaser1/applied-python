from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Iterator

DIR_PATH: Path = Path(__file__).parent.resolve()


class DirDict(MutableMapping):
    def __init__(self, directory: str):
        self._directory: Path = (DIR_PATH / directory.strip("/")).resolve()
        self._directory.mkdir(exist_ok=True)

    def _find_path(self, filename: str) -> Path:
        return self._directory / filename

    def __setitem__(self, key: str, value: str):
        if not isinstance(value, str):
            value = str(value)

        f = self._find_path(key)
        f.write_text(value)

    def __getitem__(self, key: str) -> str:
        f: Path = self._find_path(key)
        if f.is_file():
            return f.read_text()

        raise KeyError(key)

    def __delitem__(self, key: str):
        file_path: Path = self._find_path(key)

        if not file_path.exists():
            raise KeyError(key)

        Path.unlink(file_path)

    def __len__(self) -> int:
        return sum(1 for _ in self.__iter__())

    def __iter__(self) -> Iterator[str]:
        for f in self._directory.iterdir():
            if f.is_file():
                yield f.name

    def keys(self):
        return list(self)

    def values(self):
        return list((self[key] for key in self))

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key: str, default: Any = None) -> str:
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            if default is not None:
                return default
            raise KeyError

    def __str__(self):
        custom_d = {item: self._find_path(item).read_text() for item in self.__iter__()}
        return f"{custom_d}"
