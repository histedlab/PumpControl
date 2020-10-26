# ne500_behavpump:  control class for an ne500, customized for our behavior needs.
#
# created: histed 170615
#from __future__ import unicode_literals # use Py3 unicode string format when rnning on Py2
import serial
import time
import re

class NE500(object):
    """Interface with a New Era Pump Systems NE-500 using this class."""

    def __init__(self, device_name, diameter, rate, debug=False):
        """Save parameters only, setup on __enter__"""
        self.device_name = device_name
        self.diameter = diameter
        self.rate = rate
        self.rateUnits = b'MM'  # hardcoded for now
        self.volUnits = b'UL'
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
        self.send_command(b'DIA %4.2f' % self.diameter, expOutput=b'')
        self.send_command(b'RAT %4.2f %s' % (self.rate, self.rateUnits), expOutput=b'')
        self.send_command(b'VOL %s' % self.volUnits, expOutput=b'')

        return self

    def send_command(self, command, expStatus=b'S', expOutput=None):
        """Sends a command to the pump, parses status output, returns response string.
        
        expOutput: if None, return response output.  If not None, raise if output != expOutput
        expStatus: (default 'S') if not None, raise if status != expStatus and return (response string)
            if None, return full output from pump parsed into three parts: (response, num, status)

        Don't supply line endings to command, they will be added.
        Raises if status is unknown (now: not (S)topped), or if return string unknown.
        Uses basic mode.
        Should parse response string (after 00S) in other methods.


        """
        if type(command) is not bytes:
            raise RuntimeError('input must be bytes, not unicode')
        assert(command[-1] != b'\n' and command[-1] != b'\r'), 'Do not use line endings on command'
        self.ser.write(command+b'\r\n')
        if self.debug: print('out: %s' % command)
        
        while(self.ser.inWaiting() == 0):
            time.sleep(0.005)
        time.sleep(0.020) # extra 10 ms after first chars come in
        nB = self.ser.inWaiting()
        out = self.ser.read(nB)
        if self.debug: print('in : %s' % out)

        time.sleep(0.005)
        assert(self.ser.inWaiting() == 0), 'characters returned after read? : last %s' % out
        
        m0 = re.match(rb'\x02([0-9][0-9])(.)(.*)\x03', out)
        if m0 is None:
            raise RuntimeError('unknown response: %s' % out)
        num,status,response = m0.groups()
        
        if expStatus is not None and status != expStatus:
            raise RuntimeError('Unknown status from pump (not %s, is: %s)' % (expStatus, status))
        if expOutput is not None:
            if response != expOutput:
                #print(np.array(response, dtype='int'))
                #print(np.array(expOutput, dtype='int'))
                raise RuntimeError('output: "%s" is not expected: "%s"' % (response,expOutput))

        if expStatus is None:
            return(response, status, num)
        else:
            return(response)


    def get_dispensed(self):
        """command: get dispensed volume.  Returns: (infuseVol,withdrawVol,units)"""
        outS = self.send_command(b'DIS')
        #print(outS)
        m0 = re.search(r'I([0-9\.]*)W([0-9\.]*)(.L)', outS)
        infuseVol, withdrawVol, units = m0.groups()
        infuseVol = float(infuseVol)
        withdrawVol = float(withdrawVol)
        return(infuseVol, withdrawVol, units)

    def _move(self, vol, block=False, dir='infuse'):
        """instruct pump to move a specified volume.
        block: boolean, whether to wait for pump to finish
        dir: 'infuse' or 'withdraw'  """
        if dir == 'infuse':
            dir_cmd = b'INF'
            status_char = b'I'
        elif dir == 'withdraw':
            dir_cmd = b'WDR'
            status_char = b'W'
        else:
            raise RuntimeError('Invalid direction')
        
        self.send_command(b'DIR %s' % dir_cmd, expOutput=b'')
        self.send_command(b'VOL %d' % vol, expOutput=b'')
        self.send_command(b'RUN', expStatus=status_char, expOutput=b'')
        if block:
            self.wait_for_stop()


    def wait_for_stop(self):
        while self.check_status() != b'S':
            time.sleep(0.01)  # 10 ms increments
        

    def infuse(self, vol, block=True):
        """instruct pump to infuse a specified volume"""
        self._move(vol, block=block, dir='infuse')

        
    def withdraw(self, vol, block=True):
        """instruct pump to withdraw a specified volume"""
        self._move(vol, block=block, dir='withdraw')


    def check_status(self):
        """Return the status character from querying pump status"""
        resp,status,num = self.send_command(b' ', expStatus=None)
        return(status)
        

    def __exit__(self, type, value, traceback):
        self.ser.close()





