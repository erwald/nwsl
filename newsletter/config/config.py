#!/usr/bin/env python3

from typing import Optional
from dataclasses import dataclass

@dataclass
class Config():
    """This holds the user's configuration, or any exception that occurred while
    loading or reading it."""
    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    error: Optional[Exception] = None
