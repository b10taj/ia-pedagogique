"""Initialisation du module prompts."""

from prompts.diodes import PROMPT_DIODE_SIMPLE, PROMPT_DIODE_BOITES
from prompts.diode_zener import PROMPT_DIODE_ZENER_SIMPLE
from prompts.transistor import PROMPT_TRANSISTOR_BIPOLAIRE, PROMPT_INVERSEUR_BIPOLAIRE
from prompts.passive import PROMPT_DIVISEUR_TENSION
from prompts.general import PROMPT_GENERAL

__all__ = [
    "PROMPT_DIODE_SIMPLE",
    "PROMPT_DIODE_BOITES",
    "PROMPT_DIODE_ZENER_SIMPLE",
    "PROMPT_TRANSISTOR_BIPOLAIRE",
    "PROMPT_INVERSEUR_BIPOLAIRE",
    "PROMPT_DIVISEUR_TENSION",
    "PROMPT_GENERAL"
]
