import typing as t


class ExceptionGroup(Exception):
    def __init__(self, errors: t.Iterable[BaseException]) -> None:
        self.errors = list(errors)
        error_str = "error" if len(self.errors) <= 1 else "errors"
        msg = f"{len(self.errors)} {error_str} raised. {error_str.capitalize()}: [{', '.join(repr(exc) for exc in self.errors)}]"
        self.msg = msg
        super().__init__(msg)
