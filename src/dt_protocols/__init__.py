__version__ = "6.2.1"

from zuper_commons.logs import ZLogger

logger = ZLogger(__name__)
import os

path = os.path.dirname(os.path.dirname(__file__))
logger.debug(f"dt-protocols version {__version__} path {path}")

from .basics import *
from .protocol_planning import *
