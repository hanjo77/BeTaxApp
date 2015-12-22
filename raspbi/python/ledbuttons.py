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
TAXI_GPIO = 23
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
    gpio_list = [PHONE_GPIO, NETWORK_GPIO, GPS_GPIO, TAXI_GPIO, DRIVER_GPIO]


    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.setup_pins()
        self.button_pressed = False
        self.since_button_pressed = -1
        self.is_tracking = True
        self.led_list = {PHONE_KEY: Led(PHONE_GPIO),
                NETWORK_KEY: Led(NETWORK_GPIO),
                GPS_KEY: Led(GPS_GPIO),
                TAXI_KEY: Led(TAXI_GPIO),
                DRIVER_KEY: Led(DRIVER_GPIO)}

#functions for LED
    def setup_pins(self):
        GPIO.setup(self.gpio_list, GPIO.OUT)
        GPIO.setup(BUTTON_GPIO, GPIO.IN)
        GPIO.remove_event_detect(BUTTON_GPIO)
        GPIO.add_event_detect(BUTTON_GPIO, GPIO.RISING, bouncetime=200)

    def setup_led(self):
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio_list, GPIO.OUT)

    def set_led_blink(self, key, value):
        self.led_list[key].blink = value
        if not value:
            self.set_led_on(self.led_list[key].gpio)

    def get_led_blink(self, pin):
        return self.led_list[pin].blink

    def set_led_on(self,pin):
        GPIO.output(self.led_list[pin].gpio, GPIO.HIGH)

    def set_led_off(self, pin):
        GPIO.output(self.led_list[pin].gpio, GPIO.LOW)

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

class LedButtonsListener(threading.Thread):

    def __init__(self, handler):
        threading.Thread.__init__(self)
        self.handler = handler

    def run(self):
        """main method"""
        try:
            oldtime = time.time()
            blink_on = True
            print 'start handler'
            while True:
                if GPIO.event_detected(BUTTON_GPIO):
                    self.handler.is_button_pressed()
                if (self.handler.since_button_pressed > 0 and
                    time.time() - self.handler.since_button_pressed > RESET_INTERVAL):
                    self.handler.change_tracking()
                if self.handler.is_tracking:
                    if (time.time() - oldtime) > BLINK_INTERVAL:
                        for led in self.handler.led_list.itervalues():
                            if led.blink:
                                GPIO.output(led.gpio, blink_on)
                        oldtime = time.time()
                        blink_on = not blink_on
        except KeyboardInterrupt:
            pass
        except Exception:
            print 'ledbuttonrunner has a problem'
            print Exception
            z = e
            print z
        finally:
            GPIO.cleanup()
            quit()
