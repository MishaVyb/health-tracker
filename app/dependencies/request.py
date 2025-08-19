import logging
from typing import TYPE_CHECKING

from fastapi import Request as _Request
from fastapi.datastructures import State as _State

if TYPE_CHECKING:

    class State(_State):
        logger: logging.Logger

    class Request(_Request):
        state: State

else:
    Request = _Request
    State = _State
