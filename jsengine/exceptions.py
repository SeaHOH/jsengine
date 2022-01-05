# Base error classes
class Error(Exception):
    pass

# Errors due to JSEngine
class RuntimeError(Error):
    pass

# Errors due to JS script
class ProgramError(Error):
    pass
