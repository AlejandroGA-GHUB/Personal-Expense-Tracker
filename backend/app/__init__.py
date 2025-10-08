# Make app a proper Python package
from .database import init_database, get_db
from .models import Transaction, Category
from . import schemas, crud

__version__ = "1.0.0"
