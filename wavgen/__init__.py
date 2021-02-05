## Exposes API Components to User ##
from . import waveform
from . import constants
from . import utilities

## Attempts to import the Spectrum rivers' Python header ##
try:
    from .card import Card
except ImportError:
    print("Spectrum drivers missing! Card functions unavailable.")

## Suppresses unnecessary warnings from ##
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="instrumental")  # instrumental deprecation
