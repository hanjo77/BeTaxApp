# EasyCabTracker LED and Button handling
#

#Imports
import RPi.GPIO as GPIO
import time
import threading

#Constants
PHONE_GPIO = 17
NETWORK_GPIO = 27
GPS_GPIO = 22
CAR_GPIO = 23
DRIVER_GPIO = 24
BUTTON_GPIO = 25
BLINK_INTERVAL = 0.5
RESET_INTERVAL = 2
PHONE_KEY = 'phone'
NETWORK_KEY = 'network'
GPS_KEY = 'gps'
TAXI_KEY = 'car'
DRIVER_KEY = 'driver'


class Led():
    """Helper class that represents an LED"""
    def __init__(self, gpio_number):
        self.gpio = gpio_number
        self.blink = True


class LedButtonHandler():
    """Handles the button and the leds"""
    gpio_list = [PHONE_GPIO, NETWORK_GPIO, GPS_GPIO, CAR_GPIO, DRIVER_GPIO]
    led_list = {PHONE_KEY: Led(PHONE_GPIO),
                NETWORK_KEY: Led(NETWORK_GPIO),
                GPS_KEY: Led(GPS_GPIO),
                TAXI_KEY: Led(CAR_GPIO),
                DRIVER_KEY: Led(DRIVER_GPIO)}
    is_tracking = True

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.setup_pins()
        self.button_pressed = False
        self.since_button_pressed = -1

#functions for LED
    def setup_pins(self):
        GPIO.setup(self.gpio_list, GPIO.OUT)
        GPIO.setup(BUTTON_GPIO, GPIO.IN)
        GPIO.remove_event_detect(BUTTON_GPIO)
        GPIO.add_event_detect(BUTTON_GPIO, GPIO.RISING, bouncetime=200)

    def setup_led(self):
#        GPIO.setwarnings(False)
        GPIO.setup(self.gpio_list, GPIO.OUT)

    def set_led_blink(self, pin, value):
        self.led_list[pin].blink = value

    def get_led_blink(self, pin):
        return self.led_list[pin].blink

    def set_led_on(self, pin):
        GPIO.output(pin, GPIO.HIGH)

    def set_led_off(self, pin):
        GPIO.output(pin, GPIO.LOW)

    def setup_button(self):
        GPIO.setup(BUTTON_GPIO, GPIO.IN)
        GPIO.remove_event_detect(BUTTON_GPIO)
        GPIO.add_event_detect(BUTTON_GPIO, GPIO.RISING, bouncetime=200)

    def is_button_pressed(self):
        """Checks if button is clicked and if it was a doubleclick"""
        if self.button_pressed:
            self.button_pressed = False
            #Double click
            if(time.time() - self.since_button_pressed
                    < RESET_INTERVAL):
                self.since_button_pressed = -1
                for led in self.led_list.itervalues():
                    led.blink = not led.blink
#                print 'reset'
            else:
                self.since_button_pressed = time.time()
#                print 'to long since double-click'
        else:
            self.button_pressed = True
            self.since_button_pressed = time.time()
#            print 'putton pressed'

    def change_tracking(self):
        """Changes tracking"""
        self.button_pressed = False
        self.is_tracking = not self.is_tracking
        self.since_button_pressed = -1
        GPIO.output(self.gpio_list, self.is_tracking)
#        print 'tracking changed'


class LedButtonsListener(threading.Thread):

    def __init__(self, handler):
        threading.Thread.__init__(self)
        self.handler = handler

    def run(self):
        """main method"""
        try:
            oldtime = time.time()
            while True:
                if GPIO.event_detected(BUTTON_GPIO):
                    self.handler.is_button_pressed()
                if (self.handler.since_button_pressed > 0 and
                    time.time() - self.handler.since_button_pressed > RESET_INTERVAL):
                    self.handler.change_tracking()
                if self.handler.is_tracking:
                    if ((time.time() - oldtime) > BLINK_INTERVAL):
                        for led in self.handler.led_list.itervalues():
                            if led.blink:
                                GPIO.output(led.gpio, not GPIO.input(led.gpio))
                        oldtime = time.time()
        except KeyboardInterrupt:
            quit()
        except Exception:
            print Exception
        finally:
            GPIO.cleanup()