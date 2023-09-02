import RPi.GPIO as GPIO
import time
import random

class omnixie_ntdb:
    def __init__(self, DATA_PIN, CLOCK_PIN, LATCH_PIN, HV_PIN, NTDB_COUNT):
        # Set pinouts
        self.DATA_PIN = DATA_PIN
        self.CLOCK_PIN = CLOCK_PIN
        self.LATCH_PIN = LATCH_PIN
        self.HV_PIN = HV_PIN
        self.NTDB_COUNT = NTDB_COUNT

        self.data = [0,0,0,0,0]
        self.mask = 0b1111
        self.num = 0

        # Define the data for each digit (0-9) in BCD format
        self.digit_data = [
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

    # Setup GPIO pins
    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.DATA_PIN, GPIO.OUT)
        GPIO.setup(self.CLOCK_PIN, GPIO.OUT)
        GPIO.setup(self.LATCH_PIN, GPIO.OUT)
        GPIO.setup(self.HV_PIN, GPIO.OUT)

    # Shift digits through register
    def shift_out(self, digits):
        for i in range(8):
            GPIO.output(self.DATA_PIN, (digits >> i) & 0x01)
            GPIO.output(self.CLOCK_PIN, GPIO.LOW)
            GPIO.output(self.CLOCK_PIN, GPIO.HIGH)

    # Run the shift function for the full set of digits
    def display(self):
        for i in range(self.NTDB_COUNT * 5):
            self.shift_out(self.data[i])
        GPIO.output(self.LATCH_PIN, GPIO.LOW)
        GPIO.output(self.LATCH_PIN, GPIO.HIGH)

    # Convert into the bit notification
    def set_number(self, number):
        if number < 0:
            number = 0
        if number > 9999:
            number = 9999

        self.num = number

        digit_left1 = (number // 1000) % 10 if (self.mask & 0b1000) == 0b1000 else 10
        digit_left2 = (number // 100) % 10 if (self.mask & 0b0100) == 0b0100 else 10
        digit_left3 = (number // 10) % 10 if (self.mask & 0b0010) == 0b0010 else 10
        digit_left4 = number % 10 if (self.mask & 0b0001) == 0b0001 else 10

        self.data[0] = self.digit_data[digit_left4] & 0b11111111
        self.data[1] = ((self.digit_data[digit_left4] & 0b1100000000) >> 8) | ((self.digit_data[digit_left3] & 0b111111) << 2)
        self.data[2] = ((self.digit_data[digit_left3] & 0b1111000000) >> 6) | ((self.digit_data[digit_left2] & 0b1111) << 4)
        self.data[3] = ((self.digit_data[digit_left2] & 0b1111110000) >> 4) | ((self.digit_data[digit_left1] & 0b11) << 6)
        self.data[4] = ((self.digit_data[digit_left1] & 0b1111111100) >> 2)

    # Automatically set mask to turn off tubes if character does not exist on left of number
    def set_mask(self, number):
            if number < 10:
                self.mask = 0b1
            elif number < 100:
                self.mask = 0b11
            elif number < 1000:
                self.mask = 0b111
            else:
                self.mask = 0b1111
    
    # Manually set mask, for example if a tube in the middle of the sequence is desired to be turned off
    def man_set_mask(self, mask):
        self.mask = mask

    # Toggle voltage to the tubes
    def hv_enable(self, hv):
        GPIO.output(self.HV_PIN, GPIO.LOW if hv else GPIO.HIGH)

    # Flashes all numbers to prevent cathode poisoning
    def cp_prevention(self):
        orig_num = self.num
        orig_mask = self.mask

        self.man_set_mask(0b1111)
        for k in range(0,5):
            for i in range(0,10):
                j = i * 1111
                self.set_number(j)
                self.display()
                time.sleep(.25)
        
        self.man_set_mask(orig_mask)
        self.set_number(orig_num)
        self.display()


def main():
    ntdb = omnixie_ntdb(17, 27, 18, 22, 1)
    try:
        ntdb.setup()
        ntdb.hv_enable(True)
        while True:
            for i in range(0,10):
                j = i * 1111
                ntdb.set_number(j)
                ntdb.display()
                time.sleep(1) 
                ntdb.cp_prevention()
                time.sleep(1)     
    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(1)
        ntdb.hv_enable(False)
        GPIO.cleanup()

if __name__ == '__main__':
    main()
