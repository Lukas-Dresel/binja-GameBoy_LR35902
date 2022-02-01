import binaryninja

from .LR35902Arch import LR35902
LR35902.register()

from .GameBoyROMView import GameBoyRomView
GameBoyRomView.register()
