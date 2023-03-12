class PyHostingError(Exception):
    """Base error class for exceptions raised in pyhosting library code."""

    def __init__(self, code: int, msg: str) -> None:
        """Create a new exception using a code and a message."""
        super().__init__(msg)
        self.code = code
        self.msg = msg


class ConflictError(PyHostingError):
    pass


class InvalidContentError(PyHostingError):
    def __init__(self, details: str) -> None:
        super().__init__(428, details)


class EmptyContentError(InvalidContentError):
    def __init__(self) -> None:
        super().__init__("Content is empty")


class ResourceAlreadyExistsError(ConflictError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(409, f"{resource.capitalize()} already exists: {identifier}")


class PageAlreadyExistsError(ResourceAlreadyExistsError):
    def __init__(self, name: str) -> None:
        super().__init__("page", name)


class VersionAlreadyExistsError(ResourceAlreadyExistsError):
    def __init__(self, name: str, version: str) -> None:
        super().__init__("version", f"{name}/{version}")


class ResourceNotFoundError(PyHostingError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(404, f"{resource.capitalize()} not found: {identifier}")


class BlobNotFoundError(ResourceNotFoundError):
    def __init__(self, identifier: str) -> None:
        super().__init__("blob", identifier)


class PageNotFoundError(ResourceNotFoundError):
    def __init__(self, identifier: str) -> None:
        super().__init__("page", identifier)


class VersionNotFoundError(ResourceNotFoundError):
    def __init__(self, name: str, version: str) -> None:
        super().__init__("version", f"{name}/{version}")


class CannotDeleteLatestVersionError(ConflictError):
    def __init__(self, name: str, version: str) -> None:
        super().__init__(409, f"Cannot delete latest page version: {name}/{version}")


class InvalidRequestError(PyHostingError):
    def __init__(self, details: str) -> None:
        self.detials = details
        super().__init__(428, f"Invalid request: {details}")
