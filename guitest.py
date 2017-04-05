# This Python file uses the following encoding: utf-8
#setup and open serial port
import time
import serial
import numpy as np
from Tkinter import *
import ttk

ser = serial.Serial(
    port='/dev/cu.usbserial-AI02FUQP', #replace 'AI02FUQP' with each pump's unique identifier
    baudrate=19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    rtscts=False,
    dsrdtr=False,
)

ser.timeout = 2
print(ser.isOpen()) #prints boolean response

######################################

import serial
import re

class NE500():
    def __init__(self, device_name, diameter=None, rate=None, debug=False):
        """Save parameters only, setup on __enter__"""
        self.device_name = device_name
        self.diameter = diameter
        self.rate = rate
        self.rateUnits = 'MM'  # hardcoded for now
        self.volUnits = 'UL'
        self.debug = debug

    def __enter__(self):
        """Setup device"""
        self.ser = serial.Serial(
            port=self.device_name, 
            baudrate=19200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            rtscts=False,
            dsrdtr=False,
            )
        self.ser.timeout = 10                   
        assert(self.ser.isOpen() == True)       #make sure connection was initiated successfully
        
        # basic setup for both infuse and withdraw
        out = self.send_command('DIA %4.2f' % self.diameter, expOutput='')
        out = self.send_command('RAT %4.2f %s' % (self.rate, self.rateUnits), expOutput='')
        out = self.send_command('VOL %s' % self.volUnits, expOutput='')
        
        return(self)
    
    def send_command(self, command, expStatus='S', expOutput=None):
        """Sends a command to the pump, parses status output, returns response string.
        
        expOutput: if None, return response output.  If not None, raise if output != expOutput

        Don't supply line endings to command, they will be added.
        Raises if status is unknown (now: not (S)topped), or if return string unknown.
        Uses basic mode.
        Should parse response string (after 00S) in other methods.
        """
        
        assert(command[-1] != '\n' and command[-1] != '\r'), 'Do not use line endings on command'
        self.ser.write(command+'\r\n')
        if self.debug: print('out: %s' % command)
        
        while(self.ser.inWaiting() == 0):
            time.sleep(0.005)
        time.sleep(0.020) # extra 10 ms after first chars come in
        nB = self.ser.inWaiting()
        out = self.ser.read(nB)
        if self.debug: print('in : %s' % out)

        time.sleep(0.005)
        assert(self.ser.inWaiting() == 0), 'characters returned after read? : last %s' % out
        
        m0 = re.match(r'\x02([0-9][0-9])(.)(.*)\x03', out)
        #if m0 is None:
            #raise RuntimeError, 'unknown response: %s' % out
        num,status,response = m0.groups()
        
        #if status is not expStatus:
            #raise RuntimeError('Unknown status from pump (not %s, is: %s)' % (expStatus, status))
        if expOutput is not None:
            if response != expOutput:
                #print(np.array(response, dtype='int'))
                #print(np.array(expOutput, dtype='int'))
                #raise RuntimeError('output: "%s" is not expected: "%s"' % (response,expOutput))
                print(response)

        return(response)
        

    def get_dispensed(self):
        """command: get dispensed volume.  Returns: (infuseVol,withdrawVol,units)"""
        outS = self.send_command('DIS')
        print(outS)
        m0 = re.search(r'I([0-9\.]*)W([0-9\.]*)(.L)', outS)
        infuseVol,withdrawVol,units = m0.groups()
        infuseVol = float(infuseVol)
        withdrawVol = float(withdrawVol)
        return(infuseVol,withdrawVol,units)
    
    def infuse(self, vol):
        self.send_command('DIR INF', expOutput='')
        self.send_command('VOL %d' % vol, expOutput='')
        self.send_command('RUN', expStatus='I', expOutput='')
        
    def withdraw(self, vol):
        self.send_command('DIR WDR', expOutput='')
        self.send_command('VOL %d' % vol, expOutput='')
        self.send_command('RUN', expStatus='W', expOutput='')

    def purge(self):
        self.send_command('DIR INF', expOutput='')
        self.send_command('PUR', expOutput='')
        #self.send_command('RUN', expOutput='')

    def __exit__(self, type, value, traceback):
        ser.close()


def draw_500(*args):
    port = '/dev/cu.usbserial-AI02FUQP'
    with NE500(port, diameter=7.29, rate=2.0) as pump:
        pump.withdraw(500)

def draw_1000(*args):
    port = '/dev/cu.usbserial-AI02FUQP'
    with NE500(port, diameter=7.29, rate=2.0) as pump:
        pump.withdraw(1000)

def draw_1500(*args):
    port = '/dev/cu.usbserial-AI02FUQP'
    with NE500(port, diameter=7.29, rate=2.0) as pump:
        pump.withdraw(1500)

def draw_2000(*args):
    port = '/dev/cu.usbserial-AI02FUQP'
    with NE500(port, diameter=7.29, rate=2.0) as pump:
        pump.withdraw(2000)

def flush(*args):
    port = '/dev/cu.usbserial-AI02FUQP'
    with NE500(port, diameter=7.29, rate=2.0) as pump:
        pump.infuse(150)
'''
   UI SETUP   
'''

root = Tk()
root.title("Refill Pump")
mainframe = ttk.Frame(root, padding="20 20 20 20")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

ttk.Button(mainframe, text="Draw 500", command=draw_500).grid(column=1, row=1, sticky=W)
ttk.Button(mainframe, text="Draw 1000", command=draw_1000).grid(column=2, row=1, sticky=W)
ttk.Button(mainframe, text="Draw 1500", command=draw_1500).grid(column=3, row=1, sticky=W)
ttk.Button(mainframe, text="Draw 2000", command=draw_2000).grid(column=4, row=1, sticky=W)
ttk.Button(mainframe, text="Flush", command=flush).grid(column=1, row=2, sticky=W)

for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

root.bind('<Return>', flush)
root.mainloop()

#####################################################################