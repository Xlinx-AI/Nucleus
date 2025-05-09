"""
Base API class for tool endpoints in nucleus.

Provides a foundation for building consistent FastAPI tool APIs with DI, routing, and path management.
If you subclass this, don't forget to implement setup_routes, or you'll get a NotImplementedError and a headache.
"""

import logging
from fastapi import APIRouter

from abc import ABC, abstractmethod

class BaseToolAPI(ABC):
    """
    BaseToolAPI provides a skeleton for all tool-specific FastAPI endpoints.
    It handles router setup, path management, and forces you to implement setup_routes().
    """
    def __init__(self, prefix="/", tags=None):
        self.router = APIRouter(prefix=prefix, tags=tags or [])
        self.model_dir = "./models"  # For now, just a placeholder; override in subclass if needed
        self.setup_routes()
        logging.debug(f"BaseToolAPI initialized with prefix '{prefix}' and model_dir: {self.model_dir}")

    @abstractmethod
    def setup_routes(self):
        """
        Implement this in your subclass to actually add routes.
        Otherwise, you'll just get an error and an empty router.
        """
        ...