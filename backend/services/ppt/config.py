# -*- coding: utf-8 -*-
"""
PPT Config — Constantes de design e paleta Edenred.
"""

import os
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# -------------------------------------------------------------------
# PALETA EDENRED
# -------------------------------------------------------------------
EDENRED_RED = RGBColor(0xE2, 0x06, 0x13)
EDENRED_RED_DARK = RGBColor(0xC1, 0x05, 0x10)
EDENRED_CORAL = RGBColor(0xEF, 0x44, 0x44)  # error-color do CSS
EDENRED_DARK = RGBColor(0x1A, 0x1A, 0x2E)
TEXT_DARK = RGBColor(0x0F, 0x17, 0x2A)
TEXT_MUTED = RGBColor(0x64, 0x74, 0x8B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG_LIGHT = RGBColor(0xF8, 0xFA, 0xFC)
LIGHT_GRAY = RGBColor(0xF1, 0xF5, 0xF9)
BORDER_GRAY = RGBColor(0xE2, 0xE8, 0xF0)
CARD_GREEN = RGBColor(0x10, 0xB9, 0x81)
CARD_AMBER = RGBColor(0xF5, 0x9E, 0x0B)
CARD_RED = RGBColor(0xE2, 0x06, 0x13)
CARD_PURPLE = RGBColor(0x63, 0x66, 0xF1)
SUCCESS_BG = RGBColor(0xEC, 0xFD, 0xF5)
WARNING_BG = RGBColor(0xFF, 0xFB, 0xEB)
DANGER_BG = RGBColor(0xFE, 0xF2, 0xF2)
PURPLE_BG = RGBColor(0xEE, 0xF2, 0xFF)

# -------------------------------------------------------------------
# DIMENSÕES
# -------------------------------------------------------------------
SLIDE_WIDTH = Inches(13.333)   # Widescreen 16:9
SLIDE_HEIGHT = Inches(7.5)

# -------------------------------------------------------------------
# TIPOGRAFIA
# -------------------------------------------------------------------
FONT_FAMILY = "Ubuntu"

# -------------------------------------------------------------------
# ASSETS
# -------------------------------------------------------------------
LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "assets", "logo.png"
)

COVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "assets", "cover.png"
)

MINILOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "assets", "edenred-minilogo.png"
)

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "assets", "icons"
)
