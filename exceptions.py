"""Custom exceptions"""


class DatabaseConfigError(Exception):
    """Raises when database config not specified in config.json"""
    pass


class NotExist(Exception):
    """Raises when database instance not exist"""
    pass
