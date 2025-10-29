__version__ = "1.0.0"

# Make the API module importable
from . import api

# Explicitly expose the api module
__all__ = ['api']