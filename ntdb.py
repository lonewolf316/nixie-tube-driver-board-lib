import RPi.GPIO as GPIO
import time
import random

# Define the pins connected to the shift register
DATA_PIN = 17
CLOCK_PIN = 27
LATCH_PIN = 18
HV_PIN = 22
NTDB_COUNT = 1

# Define the data for each digit (0-9) in BCD format
digit_data = [
    0b0000000010, #0
	0b0010000000, #1
	0b0000010000, #2
	0b0000100000, #3
	0b0000000100, #4
	0b0000001000, #5
	0b0100000000, #6
	0b1000000000, #7
	0b0001000000, #8
	0b0000000001, #9
	0b0000000000  #display off
]

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DATA_PIN, GPIO.OUT)
    GPIO.setup(CLOCK_PIN, GPIO.OUT)
    GPIO.setup(LATCH_PIN, GPIO.OUT)
    GPIO.setup(HV_PIN, GPIO.OUT)

def shift_out(data):
    for i in range(8):
        GPIO.output(DATA_PIN, (data >> i) & 0x01)
        GPIO.output(CLOCK_PIN, GPIO.LOW)
        GPIO.output(CLOCK_PIN, GPIO.HIGH)

def display(fullnum):
    for i in range(NTDB_COUNT * 5):
        shift_out(fullnum[i])
    GPIO.output(LATCH_PIN, GPIO.LOW)
    GPIO.output(LATCH_PIN, GPIO.HIGH)    

def set_number(number, digit_display_mask):
    data = []
    if number < 0:
        number = 0
    if number > 9999:
        number = 9999
    
    digit_left1 = (number // 1000) % 10 if (digit_display_mask & 0b1000) == 0b1000 else 10
    digit_left2 = (number // 100) % 10 if (digit_display_mask & 0b0100) == 0b0100 else 10
    digit_left3 = (number // 10) % 10 if (digit_display_mask & 0b0010) == 0b0010 else 10
    digit_left4 = number % 10 if (digit_display_mask & 0b0001) == 0b0001 else 10
    
    data.append(digit_data[digit_left4] & 0b11111111)
    data.append(((digit_data[digit_left4] & 0b1100000000) >> 8) | ((digit_data[digit_left3] & 0b111111) << 2))
    data.append(((digit_data[digit_left3] & 0b1111000000) >> 6) | ((digit_data[digit_left2] & 0b1111) << 4))
    data.append(((digit_data[digit_left2] & 0b1111110000) >> 4) | ((digit_data[digit_left1] & 0b11) << 6))
    data.append(((digit_data[digit_left1] & 0b1111111100) >> 2))

    display(data)

def hv_enable(hv):
    GPIO.output(HV_PIN, GPIO.LOW if hv else GPIO.HIGH)

def main():
    try:
        setup()
        hv_enable(True)
        while True:
            set_number(random.randint(1000,9999), 0b1111)
            time.sleep(1)  # Display each number for a second
    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(1)
        hv_enable(False)
        GPIO.cleanup()

if __name__ == '__main__':
    main()
