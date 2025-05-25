class UserAlreadyExists(Exception):
    """Exception raised when trying to register a user that already exists."""

    def __init__(self, message="User with given username/email already exists"):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsException(Exception):
    """Exception raised when trying to use invalid credentials"""

    def __init__(self, message="Invalid credentials provided"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundException(Exception):
    """Exception raised when trying to get not existing user"""
    def __init__(self, message="User not found"):
        self.message = message
        super().__init__(self.message)


class ResourceAlreadyExistsException(Exception):
    """Exception raised when trying to create a resource when there is already one with the same name"""

    def __init__(self, message="Resource already exists"):
        self.message = message
        super().__init__(self.message)


class ResourceNotFoundException(Exception):
    """Exception raised when trying to access a non existent resource"""

    def __init__(self, missing_resource_name: str, message="Resource not found"):
        self.missing_resource_name = missing_resource_name
        self.message = message
        super().__init__(self.message)


class InvalidPathException(Exception):
    """Exception raised when trying to use invalid path format"""

    def __init__(self, message="Invalid path format"):
        self.message = message
        super().__init__(self.message)


class FolderNotEmptyException(Exception):
    """Exception raised when trying to do forbidden operation on not empty folder"""

    def __init__(self, message="Folder not empty"):
        self.message = message
        super().__init__(self.message)


class ForbiddenActionException(Exception):
    """Exception raised when trying to do some forbidden action (for example deleting root folder)"""

    def __init__(self, message="Action forbidden"):
        self.message = message
        super().__init__(self.message)


class RootFolderAlreadyExistsException(Exception):
    """Exception raised when trying to create an already existing root folder"""

    def __init__(self, message="Root folder already exists"):
        self.message = message
        super().__init__(self.message)


class Wrong2FAException(Exception):
    """Exception raised when given 2FA code if wrong"""

    def __init__(self, message="Wrong 2FA code"):
        self.message = message
        super().__init__(self.message)


class EmailAuthenticationError(Exception):
    """Exception raised when email authentication fails"""

    def __init__(self, message="Email authentication failed"):
        self.message = message
        super().__init__(self.message)


class EmailServiceUnavailable(Exception):
    """Exception raised when email service is unavailable"""

    def __init__(self, message="Email service is unavailable"):
        self.message = message
        super().__init__(self.message)


class ZipQueueError(Exception):
    """Exception raised when zip task is already in progress"""

    def __init__(self, message="Zip task already in progress"):
        self.message = message
        super().__init__(self.message)
