'''
Module handles the internal representation of Wayland messages and data
Also it parses Wayland protocol XML files and uses them to add additional context
(such as the names of message arguments)
'''

from . import connection
from .connection import Connection
from . import object
from .object import Object
from . import message
from .message import Message
from .arg import Arg
