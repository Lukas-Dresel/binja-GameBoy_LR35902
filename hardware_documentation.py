# (address, (name, long name, description))
# see http://marc.rawer.de/Gameboy/Docs/GBCPUman.pdf pages 35+
# and https://gbdev.io/pandocs/About.html for other registers

IO_REGISTERS = {
        0xFF02: ("SC", "Serial I/O Control (R/W), write 1 => Bit 7 starts a transfer and a 0 can be read on completion, Bit 0 switches internal and external clocks"),
        0xFF04: ("DIV", "This register is incremented at rate of 16384Hz (~16779Hz on SGB). Writing any value to this register resets it to 00h."),
        0xFF05: ("TIMA", "Timer Counter R/W"),
        0xFF00: ("P1", "Joypad Input", "Joypad Input"), # Page 35
        0xFF01: ("SB", "Serial Bus (Data R/W)", "Data is read from and written to the serial bus via this register"),
        0xFF02: ("SC", "Serial I/O Control (R/W)", "Setting Bit 7 starts a transfer, reading a 0 from it means the transfer completed. Bit 0 switches between using the internal() and external clocks"),
        0xFF04: ("DIV", "Divider Register", """This register is incremented 16384
(~16779 on SGB) times a second. Writing
any value sets it to $00."""),
        0xFF05: ("TIMA", "Timer Counter (R/W)", "This timer is incremented by a clock frequency specified by the TAC register ($FF07). The timer generates an interrupt when it overflows."),

        0xFF06: ("TMA", "Timer Modulo (R/W)", "When the TIMA overflows, this data will be loaded."),
        0xFF07: ("TAC", "Timer Control (R/W)", "Bit 2 - Timer Stop, 0=Stop Timer 1=Start Timer. Bits 1+0 - Input Clock Select"),
        0xFF0F: ("IF", "Interrupt Flag (R/W)", "Bit 4: Transition from High to Low of Pin, number P10-P13\nBit 3: Serial I/O transfer complete\nBit 2: Timer Overflow\nBit 1: LCDC (see STAT)\nBit 0: V-Blank"),
        0xFF10: ("NR10", "Sound Mode 1 register, Sweep Register (R/W)", """Bit 6-4 - Sweep Time
Bit 3 - Sweep Increase/Decrease
0: Addition (frequency increases)
1: Subtraction (frequency decreases)
Bit 2-0 - Number of sweep shift (n: 0-7)
Sweep Time:
000: sweep off - no freq change
001: 7.8 ms (1/128Hz)
010: 15.6 ms (2/128Hz)
011: 23.4 ms (3/128Hz)
100: 31.3 ms (4/128Hz)
101: 39.1 ms (5/128Hz)
110: 46.9 ms (6/128Hz)
111: 54.7 ms (7/128Hz)
The change of frequency (NR13,NR14) at
each shift is calculated by the following
formula where X(0) is initial freq & X(t-
1) is last freq:
X(t) = X(t-1) +/- X(t-1)/2^n
"""),
        0xFF11: ("NR11", "Sound Mode 1 register, Sound length/Wave pattern duty (R/W)", """Only Bits 7-6 can be read.
Bit 7-6 - Wave Pattern Duty
Bit 5-0 - Sound length data (t1: 0-63)
Wave Duty: (default: 10)
00: 12.5% ( _--------_--------_-------- )
01: 25% ( __-------__-------__------- )
10: 50% ( ____-----____-----____----- )
11: 75% ( ______---______---______--- )
Sound Length = (64-t1)*(1/256) seconds"""),
        0xFF12: ("NR12", "Sound Mode 1 register, Envelope (R/W)", """Bit 7-4 - Initial volume of envelope
Bit 3 - Envelope UP/DOWN
0: Attenuate
1: Amplify
Bit 2-0 - Number of envelope sweep
(n: 0-7) (If zero, stop
envelope operation.)
Initial volume of envelope is from 0 to
$F. Zero being no sound.
Length of 1 step = n*(1/64) seconds"""),
        0xff13: ("NR13", "Sound Mode 1 register, Frequency lo (W)", "Lower 8 bits of 11 bit frequency (x).\nNext 3 bit are in NR 14 ($FF14)"),
        0xFF14: ("NR14", "Sound Mode 1 register, Frequency hi (R/W)", """Only Bit 6 can be read.
Bit 7 - Initial (when set, sound
restarts)
Bit 6 - Counter/consecutive selection
Bit 2-0 - Frequency's higher 3 bits (x)
Frequency = 4194304/(32*(2048-x)) Hz
= 131072/(2048-x) Hz
Counter/consecutive Selection
0 = Regardless of the length data in
NR11 sound can be produced
consecutively.
1 = Sound is generated during the time
period set by the length data in
NR11. After this period the sound 1
ON flag (bit 0 of NR52) is reset.
"""),
        0xFF16: ("NR21", "Sound Mode 2 register, Sound Length; Wave Pattern Duty (R/W)", """Only bits 7-6 can be read.
Bit 7-6 - Wave pattern duty
Bit 5-0 - Sound length data (t1: 0-63)
Wave Duty: (default: 10)
00: 12.5% ( _--------_--------_-------- )
01: 25% ( __-------__-------__------- )
10: 50% ( ____-----____-----____----- )
11: 75% ( ______---______---______--- )
Sound Length = (64-t1)*(1/256) seconds"""),
        0xFF17: ("NR22", "Sound Mode 2 register, envelope (R/W)", """Bit 7-4 - Initial volume of envelope
Bit 3 - Envelope UP/DOWN
0: Attenuate
1: Amplify
Bit 2-0 - Number of envelope sweep
(n: 0-7) (If zero, stop
envelope operation.)
Initial volume of envelope is from 0 to
$F. Zero being no sound.
Length of 1 step = n*(1/64) seconds"""),
        0xFF18: ("NR23", "Sound Mode 2 register, frequency lo data (W)", "Frequency's lower 8 bits of 11 bit data\n(x). Next 3 bits are in NR 24 ($FF19)."),
        0xFF19: ("NR24", "Sound Mode 2 register, frequency hi data (R/W)", """Only bit 6 can be read.
Bit 7 - Initial (when set, sound
                restarts)
Bit 6 - Counter/consecutive selection
Bit 2-0 - Frequency's higher 3 bits (x)
Frequency = 4194304/(32*(2048-x)) Hz
= 131072/(2048-x) Hz
Counter/consecutive Selection
0 = Regardless of the length data in
NR21 sound can be produced
consecutively.
1 = Sound is generated during the time
period set by the length data in
NR21. After this period the sound 2
ON flag (bit 1 of NR52) is reset."""),
        0xFF1A: ("NR30", "Sound Mode 3 register, Sound on/off (R/W)", """Only bit 7 can be read
Bit 7 - Sound OFF
0: Sound 3 output stop
1: Sound 3 output OK"""),
        0xFF1B: ("NR31", "Sound Mode 3 register, sound length (R/W)", "Bit 7-0 - Sound length (t1: 0 - 255)\nSound Length = (256-t1)*(1/2) seconds"),
        0xFF1C: ("NR32", "Sound Mode 3 register, Select output level (R/W)", """Only bits 6-5 can be read
Bit 6-5 - Select output level
00: Mute
01: Produce Wave Pattern RAM
Data as it is(4 bit length)
10: Produce Wave Pattern RAM
data shifted once to the
RIGHT (1/2) (4 bit length)
11: Produce Wave Pattern RAM
data shifted twice to the
RIGHT (1/4) (4 bit length)
* - Wave Pattern RAM is located from $FF30-$FF3f."""),
        0xFF1D: ("NR33", "Sound Mode 3 register, frequency's lower data (W)", "Lower 8 bits of an 11 bit frequency (x)."),
        0xFF1E: ("NR34", "Sound Mode 3 register, frequency's higher data (R/W)", """Only bit 6 can be read.Bit 7 - Initial (when set,sound restarts)
Bit 6 - Counter/consecutive flag
Bit 2-0 - Frequency's higher 3 bits (x).
Frequency = 4194304/(64*(2048-x)) Hz
= 65536/(2048-x) Hz
Counter/consecutive Selection
0 = Regardless of the length data in
NR31 sound can be produced
consecutively.
1 = Sound is generated during the time
period set by the length data in
NR31. After this period the sound 3
ON flag (bit 2 of NR52) is reset."""),
        0xFF20: ("NR41", "Sound Mode 4 register, sound length (R/W)", """Bit 5-0 - Sound length data (t1: 0-63)
Sound Length = (64-t1)*(1/256) seconds"""),
        0xFF21: ("NR42", "Sound Mode 4 register, envelope (R/W)", """Bit 7-4 - Initial volume of envelope
Bit 3 - Envelope UP/DOWN
0: Attenuate
1: Amplify
Bit 2-0 - Number of envelope sweep
(n: 0-7) (If zero, stop
envelope operation.)
Initial volume of envelope is from 0 to
$F. Zero being no sound.
Length of 1 step = n*(1/64) seconds"""),
        0xFF22: ("NR43", "Sound Mode 4 register, polynomial counter (R/W)", """Bit 7-4 - Selection of the shift clock
frequency of the polynomial
counter
Bit 3 - Selection of the polynomial
counter's step
Bit 2-0 - Selection of the dividing ratio
of frequencies:
000: f * 1/2^3 * 2
001: f * 1/2^3 * 1
010: f * 1/2^3 * 1/2
011: f * 1/2^3 * 1/3
100: f * 1/2^3 * 1/4
101: f * 1/2^3 * 1/5
110: f * 1/2^3 * 1/6
111: f * 1/2^3 * 1/7
f = 4.194304 Mhz
Selection of the polynomial counter step:
0: 15 steps
1: 7 steps
Selection of the shift clock frequency of
the polynomial counter:
0000: dividing ratio of frequencies * 1/2
0001: dividing ratio of frequencies * 1/2^2
0010: dividing ratio of frequencies * 1/2^3
0011: dividing ratio of frequencies * 1/2^4
: :
: :
: :
0101: dividing ratio of frequencies * 1/2^14
1110: prohibited code
1111: prohibited code"""),
        0xFF23: ("NR44", "Sound Mode 4 register, counter/consecutive; inital (R/W)", """Only bit 6 can be read.
Bit 7 - Initial (when set, sound restarts)
Bit 6 - Counter/consecutive selection
Counter/consecutive Selection
0 = Regardless of the length data in NR41
sound can be produced consecutively.
1 = Sound is generated during the time
period set by the length data in NR41.
After this period the sound 4 ON flag
(bit 3 of NR52) is reset."""),
        0xFF24: ("NR50", "Channel control / ON-OFF / Volume (R/W)", """Bit 7 - Vin->SO2 ON/OFF
Bit 6-4 - SO2 output level (volume) (# 0-7)
Bit 3 - Vin->SO1 ON/OFF
Bit 2-0 - SO1 output level (volume) (# 0-7)
Vin->SO1 (Vin->SO2)
By synthesizing the sound from sound 1
through 4, the voice input from Vin
terminal is put out.
0: no output
1: output OK"""),
        0xFF25: ("NR51", "Selection of Sound output terminal (R/W)", """Bit 7 - Output sound 4 to SO2 terminal
Bit 6 - Output sound 3 to SO2 terminal
Bit 5 - Output sound 2 to SO2 terminal
Bit 4 - Output sound 1 to SO2 terminal
Bit 3 - Output sound 4 to SO1 terminal
Bit 2 - Output sound 3 to SO1 terminal
Bit 1 - Output sound 2 to SO1 terminal
Bit 0 - Output sound 1 to SO1 terminal"""),
        0xFF26: ("NR52", "Sound on/off (R/W)", """Bit 7 - All sound on/off
0: stop all sound circuits
1: operate all sound circuits
Bit 3 - Sound 4 ON flag
Bit 2 - Sound 3 ON flag
Bit 1 - Sound 2 ON flag
Bit 0 - Sound 1 ON flag
Bits 0 - 3 of this register are meant to
be status bits to be read. Writing to
these bits does NOT enable/disable
sound.
If your GB programs don't use sound then
write $00 to this register to save 16%
or more on GB power consumption."""),
        0xFF40: ("LCDC", "LCD Control (R/W)", """
Bit 7 - LCD Control Operation *
        0: Stop completely (no picture on screen)
        1: operation
Bit 6 - Window Tile Map Display Select
        0: $9800-$9BFF
        1: $9C00-$9FFF
Bit 5 - Window Display
        0: off
        1: on
Bit 4 - BG & Window Tile Data Select
        0: $8800-$97FF
        1: $8000-$8FFF <- Same area as OBJ
Bit 3 - BG Tile Map Display Select
        0: $9800-$9BFF
        1: $9C00-$9FFF
Bit 2 - OBJ (Sprite) Size
        0: 8*8
        1: 8*16 (width*height)
Bit 1 - OBJ (Sprite) Display
        0: off
        1: on
Bit 0 - BG & Window Display
        0: off
        1: on
* - Stopping LCD operation (bit 7 from 1 to 0) must
be performed during V-blank to work properly. V-
blank can be confirmed when the value of LY is
greater than or equal to 144."""),
        0xFF41: ("STAT", "LCDC Status (R/W)", """Bits 6-3 - Interrupt Selection By LCDC Status
Bit 6 - LYC=LY Coincidence (Selectable)
Bit 5 - Mode 10
Bit 4 - Mode 01
Bit 3 - Mode 00
0: Non Selection
1: Selection
Bit 2 - Coincidence Flag
0: LYC not equal to LCDC LY
1: LYC = LCDC LY
Bit 1-0 - Mode Flag
00: During H-Blank
01: During V-Blank
10: During Searching OAM-RAM
11: During Transfering Data to
LCD Driver
STAT shows the current status of the LCD controller.
Mode 00: When the flag is 00 it is the H-Blank
period and the CPU can access the display
RAM ($8000-$9FFF).
Mode 01: When the flag is 01 it is the V-Blank
period and the CPU can access the display
RAM ($8000-$9FFF).
Mode 10: When the flag is 10 then the OAM is being
used ($FE00-$FE9F). The CPU cannot access
the OAM during this period
Mode 11: When the flag is 11 both the OAM and
display RAM are being used. The CPU cannot
access either during this period.
The following are typical when the display is
enabled:
Mode 0:
000___000___000___000___000___000___000________________
Mode 1:
_______________________________________11111111111111__
Mode 2:
___2_____2_____2_____2_____2_____2___________________2_
Mode 3:
____33____33____33____33____33____33__________________3
The Mode Flag goes through the values 0, 2,
and 3 at a cycle of about 109uS. 0 is present
about 48.6uS, 2 about 19uS, and 3 about 41uS.
This is interrupted every 16.6ms by the VBlank
(1). The mode flag stays set at 1 for about 1.08
ms. (Mode 0 is present between 201-207 clks, 2
about 77-83 clks, and 3 about 169-175 clks. A
complete cycle through these states takes 456
clks. VBlank lasts 4560 clks. A complete screen
refresh occurs every 70224 clks.)"""),
        0xFF42: ("SCY", "Scroll Y (R/W)", "8 Bit value $00-$FF to scroll BG Y screen position."),
        0xFF43: ("SCX", "Scroll X (R/W)", "8 Bit value $00-$FF to scroll BG X screen position."),
        0xFF44: ("LY", "LCDC Y-Coordinate (R)", """The LY indicates the vertical line to which
the present data is transferred to the LCD
Driver. The LY can take on any value
between 0 through 153. The values between
144 and 153 indicate the V-Blank period.
Writing will reset the counter."""),
        0xFF45: ("LYC", "LY Compare (R/W)", """The LYC compares itself with the LY. If the
values are the same it causes the STAT to
set the coincident flag."""),
        0xFF46: ("DMA", "DMA Transfer and Start Address (W)", """The DMA Transfer (40*28 bit) from internal ROM or
RAM ($0000-$F19F) to the OAM (address $FE00-$FE9F)
can be performed. It takes 160 microseconds for the
transfer.
40*28 bit = #140 or #$8C. As you can see, it only
transfers $8C bytes of data. OAM data is $A0 bytes
long, from $0-$9F.
But if you examine the OAM data you see that 4 bits
are not in use.
40*32 bit = #$A0, but since 4 bits for each OAM is
not used it's 40*28 bit.
It transfers all the OAM data to OAM RAM.
The DMA transfer start address can be designated
every $100 from address $0000-$F100. That means
$0000, $0100, $0200, $0300....
As can be seen by looking at register $FF41 Sprite
RAM ($FE00 - $FE9F) is not always available. A
simple routine that many games use to write data to
Sprite memory is shown below. Since it copies data
to the sprite RAM at the appropriate times it
removes that responsibility from the main program.
All of the memory space, except high RAM
($FF80-$FFFE), is not accessible during DMA. Because
of this, the routine below must be copied & executed
in high ram. It is usually called from a V-blank
Interrupt.
Example program:
    org $40
    jp VBlank
    org $ff80
VBlank:
    push af <- Save A reg & flags
    ld a,BASE_ADRS <- transfer data from BASE_ADRS
    ld ($ff46),a <- put A into DMA registers
    ld a,28h <- loop length
Wait: <- We need to wait 160 ms.
    dec a <- 4 cycles - decrease A by 1
    jr nz,Wait <- 12 cycles - branch if Not Zero to Wait
    pop af <- Restore A reg & flags
    reti <- Return from interrupt
"""),
        0xFF47: ("BGP", "BG & Window Palette Data (R/W)", """Bit 7-6 - Data for Dot Data 11
(Normally darkest color)
Bit 5-4 - Data for Dot Data 10
Bit 3-2 - Data for Dot Data 01
Bit 1-0 - Data for Dot Data 00
(Normally lightest color)
This selects the shade of grays to use
for the background (BG) & window pixels.
Since each pixel uses 2 bits, the
corresponding shade will be selected from
here."""),
        0xFF48: ("OBP0", "Object Palette 0 Data (R/W)", """This selects the colors for sprite
palette 0. It works exactly as BGP
($FF47) except each each value of 0 is
transparent."""),
        0xFF49: ("OBP1", "Object Palette 1 Data (R/W)", """This Selects the colors for sprite
palette 1. It works exactly as OBP0
($FF48). See BGP for details."""),
        0xFF4A: ("WY", "Window Y Position (R/W)", """0 <= WY <= 143
WY must be greater than or equal to 0 and
must be less than or equal to 143 for
window to be visible."""),
        0xFF4B: ("WX", "Window X Position (R/W)", """0 <= WX <= 166
WX must be greater than or equal to 0 and
must be less than or equal to 166 for
window to be visible.
WX is offset from absolute screen
coordinates by 7. Setting the window to
WX=7, WY=0 will put the upper left corner
of the window at absolute screen
coordinates 0,0.
Lets say WY = 70 and WX = 87.
The window would be positioned as so:
     0                 80                159
     ______________________________________
  0 |                                      |
    |                  |                   |
    |                                      |
    |          Background Display          |
    |                 Here                 |
    |                                      |
    |                                      |
 70 |         -         +------------------|
    |                   | 80,70            |
    |                   |                  |
    |                   |  Window Display  |
    |                   |      Here        |
    |                   |                  |
    |                   |                  |
143 |___________________|__________________|
OBJ Characters (Sprites) can still enter the
window. None of the window colors are
transparent so any background tiles under the
window are hidden."""),
        0xFF4D: ("KEY1", "Prepare Speed Switch - CGB Mode Only", """ Bit 7: Current Speed     (0=Normal, 1=Double) (Read Only)
 Bit 0: Prepare Speed Switch (0=No, 1=Prepare) (Read/Write)

 This register is used to prepare the Game Boy to switch between CGB Double Speed Mode and Normal Speed Mode. The actual speed switch is performed by executing a stop instruction after Bit 0 has been set. After that, Bit 0 will be cleared automatically, and the Game Boy will operate at the "other" speed. The recommended speed switching procedure in pseudo code would be:

 IF KEY1_BIT7 != DESIRED_SPEED THEN
   IE = $00       ; (FFFF) = $00
   JOYP = $30     ; (FF00) = $30
   KEY1 = $01     ; (FF4D) = $01
   STOP
 ENDIF

 The CGB is operating in Normal Speed Mode when it is first turned on. Note that using the Double Speed Mode increases the power consumption; therefore, it would be recommended to use Single Speed whenever possible.

In Double Speed Mode the following will operate twice as fast as normal:

    The CPU (2.10 MHz, so 1 cycle = approx. 0.5 µs)
    Timer and Divider Registers
    Serial Port (Link Cable)
    DMA Transfer to OAM

And the following will keep operating as usual:

    LCD Video Controller
    HDMA Transfer to VRAM
    All Sound Timings and Frequencies

The CPU stops for 2050 cycles (= 8200 clocks) after the stop instruction is executed. During this time, the CPU is in a strange state. DIV does not tick, so some audio events are not processed. Additionally, VRAM/OAM/... locking is "frozen", yielding different results depending on the STAT mode it's started in:

    HBlank / VBlank (Mode 0 / Mode 1): The PPU cannot access any videomemory, and produces black pixels
    OAM scan (Mode 2): The PPU can access VRAM just fine, but not OAM, leading to rendering background, but not sprites
    Rendering (Mode 3): The PPU can access everything correctly, and so rendering is not affected

 """),
        0xFF4F: ("VBK", "VRAM Bank (R/W) - CGB Mode only", """This register can be written to to change VRAM banks. Only bit 0 matters, all other bits are ignored.
VRAM bank 1

VRAM bank 1 is split like VRAM bank 0 ; 8000-97FF also stores tiles (just like in bank 0), which can be accessed the same way as (and at the same time as) bank 0 tiles. 9800-9FFF contains the attributes for the corresponding Tile Maps.

Reading from this register will return the number of the currently loaded VRAM bank in bit 0, and all other bits will be set to 1.

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#ff4f---vbk---cgb-mode-only---vram-bank-rw"""),
        0xFF51: ("HDMA1", "New DMA Source, High (W) - CGB Mode only", """
These two registers specify the address at which the transfer will read data from. Normally, this should be either in ROM, SRAM or WRAM, thus either in range 0000-7FF0 or A000-DFF0. [Note: this has yet to be tested on Echo RAM, OAM, FEXX, IO and HRAM]. Trying to specify a source address in VRAM will cause garbage to be copied.

The four lower bits of this address will be ignored and treated as 0.

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#lcd-vram-dma-transfers
"""),
        0xFF52: ("HDMA2", "New DMA Source, Low (W) - CGB Mode only", """
These two registers specify the address at which the transfer will read data from. Normally, this should be either in ROM, SRAM or WRAM, thus either in range 0000-7FF0 or A000-DFF0. [Note: this has yet to be tested on Echo RAM, OAM, FEXX, IO and HRAM]. Trying to specify a source address in VRAM will cause garbage to be copied.

The four lower bits of this address will be ignored and treated as 0.

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#lcd-vram-dma-transfers
"""),
        0xFF53: ("HDMA3", "New DMA Destination, High (W) - CGB Mode only", """
These two registers specify the address within 8000-9FF0 to which the data will be copied. Only bits 12-4 are respected; others are ignored. The four lower bits of this address will be ignored and treated as 0.

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#lcd-vram-dma-transfers
"""),
        0xFF54: ("HDMA4", "New DMA Destination, Low (W) - CGB Mode only", """
These two registers specify the address within 8000-9FF0 to which the data will be copied. Only bits 12-4 are respected; others are ignored. The four lower bits of this address will be ignored and treated as 0.

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#lcd-vram-dma-transfers
"""),
        0xFF55: ("HDMA5", "New DMA Length/Mode/Start - CGB Mode only", """These registers are used to initiate a DMA transfer from ROM or RAM to VRAM. The Source Start Address may be located at 0000-7FF0 or A000-DFF0, the lower four bits of the address are ignored (treated as zero). The Destination Start Address may be located at 8000-9FF0, the lower four bits of the address are ignored (treated as zero), the upper 3 bits are ignored either (destination is always in VRAM).

Writing to this register starts the transfer, the lower 7 bits of which specify the Transfer Length (divided by 10h, minus 1), that is, lengths of 10h-800h bytes can be defined by the values 00h-7Fh. The upper bit indicates the Transfer Mode:
Bit 7 = 0 - General Purpose DMA

When using this transfer method, all data is transferred at once. The execution of the program is halted until the transfer has completed. Note that the General Purpose DMA blindly attempts to copy the data, even if the LCD controller is currently accessing VRAM. So General Purpose DMA should be used only if the Display is disabled, or during VBlank, or (for rather short blocks) during HBlank. The execution of the program continues when the transfer has been completed, and FF55 then contains a value of FFh.
Bit 7 = 1 - HBlank DMA

The HBlank DMA transfers 10h bytes of data during each HBlank, that is, at LY=0-143, no data is transferred during VBlank (LY=144-153), but the transfer will then continue at LY=00. The execution of the program is halted during the separate transfers, but the program execution continues during the "spaces" between each data block. Note that the program should not change the Destination VRAM bank (FF4F), or the Source ROM/RAM bank (in case data is transferred from bankable memory) until the transfer has completed! (The transfer should be paused as described below while the banks are switched)

Reading from Register FF55 returns the remaining length (divided by 10h, minus 1), a value of 0FFh indicates that the transfer has completed. It is also possible to terminate an active HBlank transfer by writing zero to Bit 7 of FF55. In that case reading from FF55 will return how many $10 "blocks" remained (minus 1) in the lower 7 bits, but Bit 7 will be read as "1". Stopping the transfer doesn't set HDMA1-4 to $FF.

::: warning WARNING

HBlank DMA should not be started (write to FF55) during a HBlank period (STAT mode 0).

If the transfer's destination address overflows, the transfer stops prematurely. The status of the registers if this happens still needs to be investigated.

:::
Confirming if the DMA Transfer is Active

Reading Bit 7 of FF55 can be used to confirm if the DMA transfer is active (1=Not Active, 0=Active). This works under any circumstances - after completion of General Purpose, or HBlank Transfer, and after manually terminating a HBlank Transfer.
Transfer Timings

In both Normal Speed and Double Speed Mode it takes about 8 μs to transfer a block of $10 bytes. That is, 8 M-cycles in Normal Speed Mode [1], and 16 "fast" M-cycles in Double Speed Mode [2]. Older MBC controllers (like MBC1-3) and slower ROMs are not guaranteed to support General Purpose or HBlank DMA, that's because there are always 2 bytes transferred per microsecond (even if the itself program runs it Normal Speed Mode).

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#ff55---hdma5-new-dma-lengthmodestart-w---cgb-mode-only"""),
        0xFF56: ("RP", "Infrared Communications Port - CGB Mode only", """This register allows to input and output data through the CGBs built-in Infrared Port. When reading data, bit 6 and 7 must be set (and obviously Bit 0 must be cleared - if you don't want to receive your own Game Boy's IR signal). After sending or receiving data you should reset the register to 00h to reduce battery power consumption again.

 Bit 0:   Write Data   (0=LED Off, 1=LED On)             (Read/Write)
 Bit 1:   Read Data    (0=Receiving IR Signal, 1=Normal) (Read Only)
 Bit 6-7: Data Read Enable (0=Disable, 3=Enable)         (Read/Write)

Note that the receiver will adapt itself to the normal level of IR pollution in the air, so if you would send a LED ON signal for a longer period, then the receiver would treat that as normal (=OFF) after a while. For example, a Philips TV Remote Control sends a series of 32 LED ON/OFF pulses (length 10us ON, 17.5us OFF each) instead of a permanent 880us LED ON signal. Even though being generally CGB compatible, the GBA does not include an infra-red port.

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#ff56---rp---cgb-mode-only---infrared-communications-port
"""),
        0xFF68: ("BCPS", "Background Color Palette Specification - CGB Mode only", """This register is used to address a byte in the CGB's background palette RAM. Since there are 8 palettes, 8 palettes × 4 colors/palette × 2 bytes/color = 64 bytes can be addressed.

Bit 7     Auto Increment  (0=Disabled, 1=Increment after Writing)
Bit 5-0   Address ($00-3F)

First comes BGP0 color number 0, then BGP0 color number 1, BGP0 color number 2, BGP0 color number 3, BGP1 color number 0, and so on. Thus, address $03 allows accessing the second (upper) byte of BGP0 color #1 via BCPD, which contains the color's blue and upper green bits.

Data can be read from or written to the specified CRAM address through BCPD/BGPD. If the Auto Increment bit is set, the index gets incremented after each write to BCPD. Auto Increment has no effect when reading from BCPD, so the index must be manually incremented in that case. Writing to BCPD during rendering still causes auto-increment to occur, despite the write being blocked.

Unlike BCPD, this register can be accessed outside VBlank and HBlank.

See https://github.com/gbdev/pandocs/blob/5ff8ccdd14e1bdbee1819df96902363dcd9db2ab/src/Palettes.md#ff68---bcpsbgpi-background-color-palette-specification-or-background-palette-index---cgb-mode-only"""),
        0xFF69: ("BCPD", "Background Color Palette Data - CGB Mode only", """
This register allows to read/write data to the CGBs background palette memory, addressed through BCPS/BGPI. Each color is stored as little-endian RGB555:

Bit 0-4   Red Intensity   ($00-1F)
Bit 5-9   Green Intensity ($00-1F)
Bit 10-14 Blue Intensity  ($00-1F)

Much like VRAM, data in palette memory cannot be read or written during the time when the PPU is reading from it, that is, Mode 3.

::: tip NOTE

All background colors are initialized as white by the boot ROM, however it is a good idea to initialize all colors yourself, e.g. if implementing a soft-reset mechanic.

See https://github.com/gbdev/pandocs/blob/5ff8ccdd14e1bdbee1819df96902363dcd9db2ab/src/Palettes.md#ff69---bcpdbgpd-background-color-palette-data-or-background-palette-data---cgb-mode-only"""),
        0xFF6A: ("OCPS", "OBJ Color Palette Specification", """
These registers function exactly like BCPS and BCPD respectively; the 64 bytes of OBJ palette memory are entirely separate from Background palette memory, but function the same.

Note that while 4 colors are stored per OBJ palette, color #0 is never used, as it's always transparent. It's thus fine to write garbage values, or even leave color #0 uninitialized.

::: tip NOTE

The boot ROM leaves all object colors uninitialized (and thus somewhat random), aside from setting the first byte of OBJ0 color #0 to $00, which is unused.

:::

See https://github.com/gbdev/pandocs/blob/5ff8ccdd14e1bdbee1819df96902363dcd9db2ab/src/Palettes.md#ff6a---ocpsobpi-obj-color-palette-specification--obj-palette-index-ff6b---ocpdobpd-obj-color-palette-data--obj-palette-data---both-cgb-mode-only
"""),
        0xFF6B: ("OCPD", "OBJ Color Palette Data", """
These registers function exactly like BCPS and BCPD respectively; the 64 bytes of OBJ palette memory are entirely separate from Background palette memory, but function the same.

Note that while 4 colors are stored per OBJ palette, color #0 is never used, as it's always transparent. It's thus fine to write garbage values, or even leave color #0 uninitialized.

::: tip NOTE

The boot ROM leaves all object colors uninitialized (and thus somewhat random), aside from setting the first byte of OBJ0 color #0 to $00, which is unused.

:::

See https://github.com/gbdev/pandocs/blob/5ff8ccdd14e1bdbee1819df96902363dcd9db2ab/src/Palettes.md#ff6a---ocpsobpi-obj-color-palette-specification--obj-palette-index-ff6b---ocpdobpd-obj-color-palette-data--obj-palette-data---both-cgb-mode-only
"""),
        0xFF6C: ("OPRI", "Object Priority Mode - CGB Mode only", """This register serves as a flag for which object priority mode to use. While the DMG prioritizes objects by x-coordinate, the CGB prioritizes them by location in OAM. This flag is set by the CGB bios after checking the game's CGB compatibility.

OPRI has an effect if a PGB value (0xX8, 0xXC) is written to KEY0 but STOP hasn't been executed yet, and the write takes effect instantly.

::: warning TO BE VERIFIED

It does not have an effect, at least not an instant effect, if written to during CGB or DMG mode after the boot ROM has been unmapped. It is not known if triggering a PSM NMI, which remaps the boot ROM, has an effect on this register's behavior.

:::

Bit 0: OBJ Priority Mode (0=OAM Priority, 1=Coordinate Priority) (Read/Write)

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#ff6c---opri---cgb-mode-only---object-priority-mode
"""),
        0xFF70: ("SVBK", "Select WRAM Bank", """In CGB Mode 32 KBytes internal RAM are available. This memory is divided into 8 banks of 4 KBytes each. Bank 0 is always available in memory at C000-CFFF, Bank 1-7 can be selected into the address space at D000-DFFF.

 Bit 0-2  Select WRAM Bank (Read/Write)

Writing a value of 01h-07h will select Bank 1-7, writing a value of 00h will select Bank 1 too.

See https://github.com/gbdev/pandocs/blob/c47f26c5f274faee44c0021e38452da14becbb7a/src/CGB_Registers.md#ff70---svbk---cgb-mode-only---wram-bank
"""),
        0xFFFF: ("IE", "Interrupt Enable (R/W)", """
Bit 4: Transition from High to Low of Pin
       number P10-P13.
Bit 3: Serial I/O transfer complete
Bit 2: Timer Overflow
Bit 1: LCDC (see STAT)
Bit 0: V-Blank
0: disable
1: enable"""),
}