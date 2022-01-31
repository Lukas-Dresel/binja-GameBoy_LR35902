# LR35902 Architecture & GameBoy ROM loader(v1.0)
Author: **Lukas Dresel**

## Description:

<p>
This LR35902 architecture plugin was written after a grueling CTF challenge of a GB ROM to have a building block for future challenges. None of the other plugins provided LLIL lifting at the time, so this aims to change that.
</p>

<p>
This plugin uses the <a href='https://github.com/Lukas-Dresel/lr35902dis'>lr35902</a> library for disassembly, and was rather unceremoniously ripped straight from Vector 35's <a href='https://github.com/Vector35/Z80'>Z80</a> plugin and modified to support the opcodes of the LR35902 CPU.
It also contains a GameBoyRomView straight up stolen from <a href='https://github.com/ZetaTwo/binja-gameboy'>ZetaTwo's Improved GameBoyRom plugin</a>.
</p>

<p>
The aim is to be able to lift the entire LR35902 instruction set to LLIL accurately. If you find any instructions lifted incorrectly, please create an Issue or a Pull Request.
</p>

## Installation Instructions

### Windows

The built-in Python 2.7 currently included in Windows builds can't easily have additional dependencies installed. We recommend installing a 64-bit version of python, using the native pip functionality to install the lr35902dis module.

### Linux

pip install lr35902dis; pip3 install lr35902dis

### Darwin

pip install lr35902dis; pip3 install lr35902dis

## Minimum Version

This plugin requires the following minimum version of Binary Ninja:

* 776



## Required Dependencies

The following dependencies are required for this plugin:

 * pip - lr35902


## License

This plugin is released under a MIT license.
## Metadata Version

2
