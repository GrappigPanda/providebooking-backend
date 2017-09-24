from http import HTTPStatus


class BaseAlmanacException(Exception):
    """
    The base exception class used for all other base exceptions.
    """

    def __init__(self, msg, status_code=400):
        self.msg = msg
        self.status_code = status_code


class SQLException(BaseAlmanacException):
    pass


class DAOException(BaseAlmanacException):
    pass


class TableException(BaseAlmanacException):
    pass


class EndpointException(BaseAlmanacException):
    pass


class HookException(BaseAlmanacException):
    pass


class ModelException(BaseAlmanacException):
    pass


class IntegrationException(BaseAlmanacException):
    pass


class FacadeException(BaseAlmanacException):
    pass


class SecurityException(BaseAlmanacException):
    def __init__(self, msg):
        super().__init__(msg, HTTPStatus.UNAUTHORIZED)
