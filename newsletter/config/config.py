#!/usr/bin/env python3

from typing import Optional
from dataclasses import dataclass

@dataclass
class Config():
    """This holds the user's configuration, or any exception that occurred while
    loading or reading it."""
    sender: Optional[str] = None
    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    error: Optional[Exception] = None

    @classmethod
    def from_json(cls, json):
        """Creates a Config object from a deserialised JSON object."""
        return Config(json['sender'], json['host'], json['user'], json['password'])

