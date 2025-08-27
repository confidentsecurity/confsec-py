from abc import ABC, abstractmethod


class Closeable(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._closed = False

    @abstractmethod
    def _close(self) -> None:
        pass

    def close(self) -> None:
        if not self._closed:
            self._close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
