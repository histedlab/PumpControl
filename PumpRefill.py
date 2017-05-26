"""This module creates a GUI for controlling an NE500 Pump"""
# This Python file uses the following encoding: utf-8

import time
try:
    import Tkinter as tk
    import ttk
except ImportError:
    import tkinter as tk
    from tkinter import ttk
import re
import serial

#replace 'AI02FUQP' with each pump's unique identifier cu.usbserial-AI02FUQP
#port = '/dev/cu.usbserial-AI02FUQP'
port = '/usr/local/dev/cu-NE500-0'
#use 7.27 for new syringes, 7.29 for old
syringe_diameter = 7.27
#rate of 2.0 > 33.3uL/sec, 1.5/3.0 > 25uL/sec 1.0/4.0 > 16.7uL/sec, 0.5, 2.5 > 8.3uL/sec
pump_rate = 2.0

# setup and open serial port
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
    """Interface with a New Era Pump Systems NE-500 using this class."""
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
        assert self.ser.isOpen() == True       #make sure connection was initiated successfully

        # basic setup for both infuse and withdraw
        self.send_command('DIA %4.2f' % self.diameter, expOutput='')
        self.send_command('RAT %4.2f %s' % (self.rate, self.rateUnits), expOutput='')
        self.send_command('VOL %s' % self.volUnits, expOutput='')

        return self

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
        if self.debug:
            print('out: %s' % command)

        while self.ser.inWaiting() == 0:
            time.sleep(0.005)
        time.sleep(0.020) # extra 10 ms after first chars come in
        nB = self.ser.inWaiting()
        out = self.ser.read(nB)
        if self.debug:
            print('in : %s' % out)

        time.sleep(0.005)
        assert(self.ser.inWaiting() == 0), 'characters returned after read? : last %s' % out

        m0 = re.match(r'\x02([0-9][0-9])(.)(.*)\x03', out)
        #if m0 is None:
            #raise RuntimeError, 'unknown response: %s' % out
        response = m0.groups()

        #if status is not expStatus:
            #raise RuntimeError('Unknown status from pump (not %s, is: %s)' % (expStatus, status))
        if expOutput is not None:
            if response != expOutput:
                #print(np.array(response, dtype='int'))
                #print(np.array(expOutput, dtype='int'))
                #raise RuntimeError('output: "%s" is not expected: "%s"' % (response,expOutput))
                print(response)

        return response


    def get_dispensed(self):
        """command: get dispensed volume.  Returns: (infuseVol,withdrawVol,units)"""
        outS = self.send_command('DIS')
        print(outS)
        m0 = re.search(r'I([0-9\.]*)W([0-9\.]*)(.L)', outS)
        infuseVol, withdrawVol, units = m0.groups()
        infuseVol = float(infuseVol)
        withdrawVol = float(withdrawVol)
        return(infuseVol, withdrawVol, units)

    def infuse(self, vol):
        """instruct pump to infuse a specified volume"""
        self.send_command('DIR INF', expOutput='')
        self.send_command('VOL %d' % vol, expOutput='')
        self.send_command('RUN', expStatus='I', expOutput='')

    def withdraw(self, vol):
        """instruct pump to withdraw a specified volume"""
        self.send_command('DIR WDR', expOutput='')
        self.send_command('VOL %d' % vol, expOutput='')
        self.send_command('RUN', expStatus='W', expOutput='')

    def __exit__(self, type, value, traceback):
        ser.close()

def refill(volume):
    """Instantiate class NE500 to interface with pump, infuse 100, and withdraw specified volume"""
    with NE500(port, syringe_diameter, pump_rate) as pump:
        pump.infuse(100)
        time.sleep(4)
        pump.withdraw(volume)

def draw_500():
    """calls refill() to push 100 and pull 500"""
    refill(500)

def draw_1000():
    """calls refill() to push 100 and pull 1000"""
    refill(1000)

def draw_1500():
    """calls refill() to push 100 and pull 1500"""
    refill(1500)

def draw_2000():
    """calls refill() to push 100 and pull 2000"""
    refill(2000)

def draw_custom():
    """calls refill() to push 100 and pull custom value from UI"""
    with NE500(port, syringe_diameter, pump_rate) as pump:
    	volume = int(customDraw.get())
    	pump.withdraw(volume)

def pump_custom():
    """pushes custom value from UI"""
    with NE500(port, syringe_diameter, pump_rate) as pump:
    	volume = int(customInfuse.get())
        pump.infuse(volume)

def clearLine():
    """pushes 200 uL"""
    with NE500(port, syringe_diameter, pump_rate) as pump:
        pump.infuse(200)
        time.sleep(7)

def changeDiameter():
    """changes diameter based on UI input, doesn't currently work"""
    syringe_diameter = float(customDiameter.get())
    diameterLabel.set('Diameter = ' + str(syringe_diameter))
    infoLabel.set('Diameter = ' + str(syringe_diameter) + '   |   Rate = ' + str(pump_rate))

def changeRate():
    """changes rate based on UI input, doesn't currently work"""
    pump_rate = float(customRate.get())
    rateLabel.set('Rate = ' + str(pump_rate))
    infoLabel.set('Diameter = ' + str(syringe_diameter) + '   |   Rate = ' + str(pump_rate))

### UI SETUP ###

root = tk.Tk()
root.title("Refill Pump")
mainframe = ttk.Frame(root, padding="20 20 20 20")
mainframe.grid(column=0, row=0)
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

ttk.Button(mainframe, width=10, text="Draw 500", command=draw_500).grid(column=1, row=1)
ttk.Button(mainframe, width=10, text="Draw 1000", command=draw_1000).grid(column=2, row=1)
ttk.Button(mainframe, width=10, text="Draw 1500", command=draw_1500).grid(column=1, row=2)
ttk.Button(mainframe, width=10, text="Draw 2000", command=draw_2000).grid(column=2, row=2)
clear_line_button = ttk.Button(mainframe, width=25, text="Clear Line", command=clearLine)
clear_line_button.grid(column=1, row=3, columnspan=2)

ttk.Label(mainframe, text='').grid(column=1, row=4)
ttk.Label(mainframe, text='').grid(column=1, row=8)

customDraw = tk.StringVar()
ttk.Label(mainframe, text='Withdraw/Pump Custom Volume').grid(column=1, row=5, columnspan=2)
ttk.Entry(mainframe, width=10, textvariable=customDraw).grid(column=1, row=6)
ttk.Button(mainframe, width=10, text="Draw", command=draw_custom).grid(column=2, row=6)

customInfuse = tk.StringVar()
ttk.Entry(mainframe, width=10, textvariable=customInfuse).grid(column=1, row=7)
ttk.Button(mainframe, width=10, text="Pump", command=pump_custom).grid(column=2, row=7)

infoLabel = tk.StringVar()
infoLabel.set('Diameter = ' + str(syringe_diameter) + '   |   Rate = ' + str(pump_rate))
ttk.Label(mainframe, textvariable=infoLabel).grid(column=1, row=9, columnspan=2)

diameterLabel = tk.StringVar()
diameterLabel.set('Diameter = ' + str(syringe_diameter))
customDiameter = tk.StringVar()
#ttk.Entry(mainframe, width=10, textvariable=customDiameter).grid(column=1, row=10)
#ttk.Button(mainframe, width=10, text="Set Diameter", command=changeDiameter).grid(column=2, row=10)

rateLabel = tk.StringVar()
rateLabel.set('Rate = ' + str(pump_rate))
customRate = tk.StringVar()
#ttk.Entry(mainframe, width=10, textvariable=customRate).grid(column=1, row=11)
#ttk.Button(mainframe, width=10, text="Set Rate", command=changeRate).grid(column=2, row=11)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

#root.bind('<Return>', clearLine)
root.mainloop()
