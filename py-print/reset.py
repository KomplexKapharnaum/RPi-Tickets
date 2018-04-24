#!/usr/bin/python

from escpos.printer import Usb
import sys

p = Usb(0x04b8,0x0e15,0)
# Control characters
# as labelled in http://www.novopos.ch/client/EPSON/TM-T20/TM-T20_eng_qr.pdf
NUL = b'\x00'
EOT = b'\x04'
ENQ = b'\x05'
DLE = b'\x10'
DC4 = b'\x14'
CAN = b'\x18'
ESC = b'\x1b'
FS  = b'\x1c'
GS  = b'\x1d'

# Feed control sequences
CTL_LF = b'\n'              # Print and line feed
CTL_FF = b'\f'              # Form feed
CTL_CR = b'\r'              # Carriage return
CTL_HT = b'\t'              # Horizontal tab
CTL_SET_HT = ESC + b'\x44'  # Set horizontal tab positions
CTL_VT = b'\v'              # Vertical tab

# Printer hardware
HW_INIT   = ESC + b'@'             # Clear data in buffer and reset modes
HW_SELECT = ESC + b'=\x01'         # Printer select

HW_RESET  = ESC + b'\x3f\x0a\x00'   # Reset printer hardware

def i():
	i.i+=1
#	print("{}".format(i.i))
i.i = 0


p.device.write(p.out_ep, HW_INIT, 1000)
i()
p.device.write(p.out_ep, HW_INIT, 1000)
i()
p.device.reset()
i()
p.device.reset()
i()
p.device.reset()
i()
#p.device.reset()
p.device.reset()
p.device.reset()
#p.device.reset()
#p.device.reset()
#p.device.reset()

i()
p.device.write(p.out_ep, HW_INIT, 1000)
#p.device.write(p.out_ep, HW_SELECT, 1000)
#p.device.write(p.out_ep, HW_RESET, 1000)
i()


#p.image("/tmp/blank.jpg", impl='bitImageColumn')
p.image("/tmp/blank.jpg", fragment_height=2500, impl='graphics', high_density_vertical=False, high_density_horizontal=False)
i()
#p.cut()
i()



