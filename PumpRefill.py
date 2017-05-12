# This Python file uses the following encoding: utf-8
# setup and open serial port
import time
import serial
import re
import numpy as np
from Tkinter import *
import ttk

#replace 'AI02FUQP' with each pump's unique identifier cu.usbserial-AI02FUQP
port = '/usr/local/dev/cu-NE500-0'
diameter = 7.29
rate = 10.0

ser = serial.Serial(
    port, 
    baudrate=19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    rtscts=False,
    dsrdtr=False,
)

ser.timeout = 2

######################################

class NE500():
    def __init__(self, device_name, diameter, rate, debug=False):
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

    def __exit__(self, type, value, traceback):
        ser.close()

def refill(volume):
    with NE500(port, diameter, rate) as pump: 
        pump.infuse(100)
        time.sleep(3)
        pump.withdraw(volume)

def draw_500(*args):
    refill(500)

def draw_1000(*args):
    refill(1000)

def draw_1500(*args):
    refill(1500)

def draw_2000(*args):
    refill(2000)

def draw_custom(*args):
    refill(int(customDraw.get()))

def pump_custom(*args):
    with NE500(port, diameter, rate) as pump:
        pump.infuse(int(customInfuse.get()))

def clearLine(*args):
    with NE500(port, diameter, rate) as pump:
        pump.infuse(200)

def changeDiameter(*args):
    diameter = float(customDiameter.get())
    dchange = True
    diameterLabel.set('Diameter = ' + str(diameter))
    infoLabel.set('Diameter = ' + str(diameter) + '   |   Rate = ' + str(rate))

def changeRate(*args):
    rate = float(customRate.get())
    rchange = True
    rateLabel.set('Rate = ' + str(rate))
    infoLabel.set('Diameter = ' + str(diameter) + '   |   Rate = ' + str(rate))

'''
   UI SETUP   
'''

root = Tk()
root.title("Refill Pump")
mainframe = ttk.Frame(root, padding="20 20 20 20")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

ttk.Button(mainframe, width=10, text="Draw 500", command=draw_500).grid(column=1, row=1)
ttk.Button(mainframe, width=10, text="Draw 1000", command=draw_1000).grid(column=2, row=1)
ttk.Button(mainframe, width=10, text="Draw 1500", command=draw_1500).grid(column=1, row=2)
ttk.Button(mainframe, width=10, text="Draw 2000", command=draw_2000).grid(column=2, row=2)
ttk.Button(mainframe, width=25, text="Clear Line", command=clearLine).grid(column=1, row=3, columnspan=2)

ttk.Label(mainframe, text='').grid(column=1, row=4)
ttk.Label(mainframe, text='').grid(column=1, row=8)

customDraw = StringVar()
ttk.Label(mainframe, text='Withdraw/Pump Custom Volume').grid(column=1, row=5, columnspan=2)
ttk.Entry(mainframe, width=10, textvariable=customDraw).grid(column=1, row=6)
ttk.Button(mainframe, width=10, text="Draw", command=draw_custom).grid(column=2, row=6)

customInfuse = StringVar()
ttk.Entry(mainframe, width=10, textvariable=customInfuse).grid(column=1, row=7)
ttk.Button(mainframe, width=10, text="Pump", command=pump_custom).grid(column=2, row=7)

infoLabel = StringVar()
infoLabel.set('Diameter = ' + str(diameter) + '   |   Rate = ' + str(rate))
ttk.Label(mainframe, textvariable=infoLabel).grid(column=1, row=9, columnspan=2)

diameterLabel = StringVar()
diameterLabel.set('Diameter = ' + str(diameter))
customDiameter = StringVar()
#ttk.Entry(mainframe, width=10, textvariable=customDiameter).grid(column=1, row=10)
#ttk.Button(mainframe, width=10, text="Set Diameter", command=changeDiameter).grid(column=2, row=10)

rateLabel = StringVar()
rateLabel.set('Rate = ' + str(rate))
customRate = StringVar()
#ttk.Entry(mainframe, width=10, textvariable=customRate).grid(column=1, row=11)
#ttk.Button(mainframe, width=10, text="Set Rate", command=changeRate).grid(column=2, row=11)

for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

#root.bind('<Return>', clearLine)
root.mainloop()

#####################################################################
