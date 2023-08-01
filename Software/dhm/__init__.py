#INIT DHM CLASS
"""
  License: GPL
  Top level classes and bolierplates licensed from https://github.com/jvzonlab/OrganoidTracker/ 
"""

class UserError(Exception):
    """Used for errors that are not the fault of the programmer, but of the user."""

    title: str
    body: str

    def __init__(self, title: str, message: str):
        super().__init__(title + "\n" + message)
        self.title = title
        self.body = message
