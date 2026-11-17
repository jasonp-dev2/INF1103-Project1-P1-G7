class DataAccessError(Exception):
    """A storage read failed; callers must not treat this as empty data."""
