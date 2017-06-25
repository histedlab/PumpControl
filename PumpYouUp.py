# This Python file uses the following encoding: utf-8


"""This module creates a GUI for controlling an NE500 Pump"""


import time
import ne500_behavpump as ne500
try:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
except ImportError:  # for Py3
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
import re

device = '/usr/local/dev/cu-NE500-0'

syringe_diameter = 7.27  #use 7.27 for new syringes, 7.29 for old
pump_rate = 2.0  #rate of 2.0 > 33.3µL/sec, 1.5/3.0 > 25µL/sec 1.0/4.0 > 16.7µL/sec, 0.5, 2.5 > 8.3µL/sec

######################################

def refill(pump, amtUl=None):
    pump.infuse(100)
    pump.withdraw(amtUl)

class ourNe500(ne500.NE500):
    """Extend original NE500 class.  Adds tracking total vol; adds refill() method"""
    totalVol = None
    volThresh = 2000  # in uL

    def __init__(self, device_name, diameter,  rate, debug=False):
        self.totalVol = 0
        super(ourNE500, self).__init__(device_name, diameter, rate, debug)

    def infuse(self, vol, block=True):
        self.totalVol += vol
        if self.totalVol >= volThresh:
            res = messagebox.askokcancel("PumpYouUp",
                                         "Total volume infused this session will exceed %dµL.  OK to continue?"%self.volThresh,
                                         icon='warning')
            if res:
                pass # continue
            else:
                self.totalVol -= vol  # reset volume to before this call
                return  # skip calling super method
        super(ourNE500, self).infuse(vol, block)


    def withdraw(self, vol, block=True):
        self.totalVol -= vol
        if self.totalVol <= -volThresh:
            res = messagebox.askokcancel("PumpYouUp",
                                         "Total volume withdrawn this session will exceed %dµL.  OK to continue?"% self.volThresh,
                                         icon='warning')
            if res:
                pass # continue
            else:
                self.totalVol -= vol  # reset volume to before this call
                return  # skip calling super method
        super(ourNE500, self).withdraw(vol, block)

    def refill(self, amtUl=None):
        """Blocking"""
        self.infuse(100)
        self.withdraw(amtUl)

######################################
        
def run_ui():

    with ourNe500(device, diameter=syringe_diameter, rate=pump_rate) as pump:
        root = tk.Tk()
        root.title("Refill Pump")
        mainframe = ttk.Frame(root, padding="20 20 20 20")
        mainframe.grid(column=0, row=0)
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        ttk.Label(mainframe, text='Pump 100µL to clear bubbles,\nthen refill indicated µL').grid(column=1, row=1, columnspan=2)
        ttk.Button(mainframe, width=10, text="Refill 500µL",
                   command=lambda: pump.refill(500)).grid(column=1, row=3)
        ttk.Button(mainframe, width=10, text="Refill 1000µL",
                   command=lambda: pump.refill(1000)).grid(column=2, row=3)
        ttk.Button(mainframe, width=10, text="Refill 1500µL",
                   command=lambda: pump.refill(1500)).grid(column=1, row=4)
        ttk.Button(mainframe, width=10, text="Refill 2000µL",
                   command=lambda: pump.refill(2000)).grid(column=2, row=4)

        ttk.Separator(mainframe,orient=tk.HORIZONTAL).grid(row=5, column=1, columnspan=2,sticky='ew', ipady='20')

        ttk.Label(mainframe, text='Pump 200µL to clear the line.').grid(column=1, row=6, columnspan=2)
        clear_line_button = ttk.Button(mainframe, width=10, text="Clear",
                                       command=lambda: pump.infuse(200))
        clear_line_button.grid(column=1, row=7, columnspan=1)

        def cbClearAndQuit():
            pump.infuse(200)
            root.destroy()
            #sys.exit(0)  # destroy will exit
        clear_line2_button = ttk.Button(mainframe, width=11, text="Clear then quit",
                                        command=cbClearAndQuit)
        clear_line2_button.grid(column=2, row=7, columnspan=1)

        
        ttk.Separator(mainframe,orient=tk.HORIZONTAL).grid(row=8, column=1, columnspan=2,sticky='ew', ipady='20')

        ttk.Label(mainframe, text='Withdraw/Pump custom µL').grid(column=1, row=9, columnspan=2)

        customWithdraw = tk.StringVar()
        customWithdraw.set(100)
        ttk.Entry(mainframe, width=10, textvariable=customWithdraw,
                  justify=tk.CENTER).grid(column=1, row=10)
        def cbWithdraw():
            pump.withdraw(float(customWithdraw.get()))
        ttk.Button(mainframe, width=10, text="Withdraw", command=cbWithdraw).grid(column=2, row=10)

        
        customPump = tk.StringVar()
        customPump.set(100)
        ttk.Entry(mainframe, width=10, textvariable=customPump,
                  justify=tk.CENTER).grid(column=1, row=11)
        def cbPump():
            pump.infuse(float(customPump.get()))
        ttk.Button(mainframe, width=10, text="Pump", command=cbPump).grid(column=2, row=11)

        ttk.Separator(mainframe,orient=tk.HORIZONTAL).grid(row=12, column=1, columnspan=2,sticky='ew', ipady='20')
        
        infoLabel = tk.StringVar()
        infoLabel.set('Diameter = ' + str(syringe_diameter) + '   |   Rate = 33µL/sec')
        ttk.Label(mainframe, textvariable=infoLabel).grid(column=1, row=13, columnspan=2)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        root.mainloop()


if __name__ == '__main__':
    run_ui()
