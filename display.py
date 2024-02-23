from machine import Pin, SPI
import max7219
spi = SPI(0, baudrate=100_000, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
#ss = Pin(5, Pin.OUT)

display = max7219.SevenSegment(digits=8, scan_digits=8, cs=5, spi_bus=spi, reverse=True)
display.brightness(1)