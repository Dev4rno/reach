from fastapi.exceptions import HTTPException

class DataNotFoundError(Exception):
    def __init__(self, entity_name: str, identifier: str, message: str = None):
        self.entity_name = entity_name
        self.identifier = identifier
        self.message = message or f"{entity_name} with identifier {identifier} not found."
        super().__init__(self.message)

    def __str__(self):
        return f"DataNotFoundError: {self.message}"
    
class DataIntegrityError(Exception):
    def __init__(self, entity_name: str, message: str = None):
        self.entity_name = entity_name
        self.message = message or f"Data integrity issue with {entity_name}."
        super().__init__(self.message)

    def __str__(self):
        return f"DataIntegrityError: {self.message}"
    
class DatabaseConnectionError(Exception):
    def __init__(self, message: str = "Unable to connect to the database.", details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        return f"DatabaseConnectionError: {self.message} Details: {self.details or 'No further details provided.'}"

class FileNotFoundError(Exception):
    def __init__(self, filename: str, message: str = None):
        self.filename = filename
        self.message = message or f"Required file '{filename}' not found."
        super().__init__(self.message)

    def __str__(self):
        return f"FileNotFoundError: {self.message}"

class RepositoryError(Exception):
    def __init__(self, message: str = "An unexpected error occurred in the repository.", details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        return f"RepositoryError: {self.message} Details: {self.details or 'No further details provided.'}"

class EntityNotFoundError(Exception):
    def __init__(self, entity_name: str, identifier: str, message: str = None):
        self.entity_name = entity_name
        self.identifier = identifier
        self.message = message or f"{entity_name} not found [{identifier}]."
        super().__init__(self.message)

    def __str__(self):
        return f"EntityNotFoundError: {self.message}"

class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"ValidationError: Field '{self.field}' - {self.message}"

class OperationNotAllowedError(Exception):
    def __init__(self, action: str, user_role: str, message: str = None):
        self.action = action
        self.user_role = user_role
        self.message = message or f"User with role {user_role} is not allowed to perform action: {action}."
        super().__init__(self.message)

    def __str__(self):
        return f"OperationNotAllowedError: {self.message}"

class ServiceLevelError(Exception):
    def __init__(self, message: str = "An unexpected service-level error occurred."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"ServiceLevelError: {self.message}"

class InvalidTokenException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)