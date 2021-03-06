#!/usr/bin/env python3

from typing import Optional
from dataclasses import dataclass

@dataclass
class Config():
    """This holds the user's configuration, or any exception that occurred while
    loading or reading it."""
    sender: Optional[str] = None
    imap_host: Optional[str] = None
    imap_user: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_user: Optional[str] = None
    error: Optional[Exception] = None

    @classmethod
    def from_json(cls, json):
        """Creates a Config object from a deserialised JSON object."""
        return Config(json['sender'],
                      json['imap_host'],
                      json['imap_user'],
                      json['smtp_host'],
                      json['smtp_user'])

