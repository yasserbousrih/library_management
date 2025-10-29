__version__ = "1.0.0"

# Make modules importable
from . import hooks
from . import desktop
from . import doctype

# Import API from parent directory and make it available as a submodule
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import api
    # Make it available in this module
    globals()['api'] = api
    # Also make it available as a submodule for frappe.get_attr
    sys.modules['library_management.api'] = api
except ImportError:
    # API module not available
    api = None