DEVICE  = atmega32
F_CPU   = 12000000	# in Hz

CFLAGS  = -Iusbdrv -I. -DDEBUG_LEVEL=0
OBJECTS = usbdrv/usbdrv.o usbdrv/usbdrvasm.o usbdrv/oddebug.o main.o

COMPILE = avr-gcc -mmcu=$(DEVICE)  $(CFLAGS) -Os -Wall -DF_CPU=$(F_CPU) 

hex: main.elf
	rm -f main.hex main.eep.hex
	avr-objcopy -j .text -j .data -O ihex main.elf main.hex
	avr-size main.elf

main.elf: $(OBJECTS)
	$(COMPILE) -o main.elf $(OBJECTS)

clean:
	rm -f main.hex main.lst main.obj main.cof main.list main.map main.eep.hex main.elf *.o usbdrv/*.o main.s usbdrv/oddebug.s usbdrv/usbdrv.s

fuse:
#	avrdude -P usb -c usbasp -p m8 -U lfuse:w:??:m

load:
	avrdude -P usb -c usbasp -p m32 -U flash:w:main.hex:i

# Generic rule for compiling C files:
.c.o:
	$(COMPILE) -c $< -o $@

# Generic rule for assembling Assembler source files:
.S.o:
	$(COMPILE) -x assembler-with-cpp -c $< -o $@
# "-x assembler-with-cpp" should not be necessary since this is the default
# file type for the .S (with capital S) extension. However, upper case
# characters are not always preserved on Windows. To ensure WinAVR
# compatibility define the file type manually.

