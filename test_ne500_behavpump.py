# unit tests for the ne500 library
# created: 170615 histed

import unittest
import ne500_behavpump as ne500
import time

device = '/usr/local/dev/cu-NE500-0'    # put a link here to your local USB device

class TestOneOff(unittest.TestCase):

    def test_setup_and_infuse(self):
        # hardcoded diameter, rate
        with ne500.NE500(device, diameter=7.27, rate=2.0) as pump:
            #print(pump.get_dispensed())
    
            pump.infuse(2)  # units in UL
            time.sleep(0.05)


class TestFull(unittest.TestCase):

    def setUp(self):
        self.pump = ne500.NE500(device, diameter=7.27, rate=2.0)
        self.pump.__enter__()

    def test_block_noblock(self):
        self.pump.infuse(5, block=True)
        self.assertEqual(self.pump.check_status(), 'S')
        self.pump.infuse(5, block=False)
        self.assertEqual(self.pump.check_status(), 'I')
        self.pump.wait_for_stop()
        
    def test_get_dispensed(self):
        p = self.pump.get_dispensed()
        # should be zero at start
        self.assertEqual(p[0], 0.0)
        self.assertEqual(p[1], 0.0)
        self.assertEqual(p[2], 'UL')

        volUl=0
        for iP in range(10):
            incUl = 2
            self.pump.infuse(incUl)
            volUl += incUl

            p = self.pump.get_dispensed()
            print(p)  #Note there will be a fractional part, we ignore it, only ~1% error
            self.assertEqual(int(p[0]), volUl)


    def tearDown(self):
        self.pump.__exit__(None, None, None)




        
if __name__ == '__main__':
    unittest.main()

