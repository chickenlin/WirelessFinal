#!/usr/bin/env python3
# -*- coding: utf8 -*-
""" A simple beacon transmitter class to send a 1-byte message (0x0f) in regular time intervals. """
# Copyright 2015 Mayer Analytics Ltd.
#
# This file is part of pySX127x.
#
# pySX127x is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pySX127x is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You can be released from the requirements of the license by obtaining a commercial license. Such a license is
# mandatory as soon as you develop commercial activities involving pySX127x without disclosing the source code of your
# own applications, or shipping pySX127x with a closed source product.
#
# You should have received a copy of the GNU General Public License along with pySX127.  If not, see
# <http://www.gnu.org/licenses/>.


from time import sleep
import json
import packer
import time
import sys
sys.path.insert(0, '../')
from SX127x.LoRa import *
from SX127x.board_config import BOARD
import numpy as np

# Use for I2C bus
import smbus
bus = smbus.SMBus(1)
address = 0x04

def readNumber():
    number = bus.read_byte(address)
    return number

BOARD.setup()

try:
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


class LoRaBeacon(LoRa):
    def __init__(self, verbose=False):
        super(LoRaBeacon, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        #self.set_dio_mapping([0,0,0,0,0,0])    # RX
        self.set_dio_mapping([1,0,0,0,0,0])    # TX
        self._id = "NODE_00"
        self.rx_done = False

    def on_rx_done(self):
        print("\nRxDone")
        print('----------------------------------')
        payload = self.read_payload(nocheck=True)
        data = ''.join([chr(c) for c in payload])

        try:
            _length, _data = packer.Unpack_Str(data)
            if _data.split(',')[0].split(":")[1][2:-1] == self._id:
                print("Time: {}".format(str(time.ctime())))
                print("Raw RX: {}".format(data))
                
                # 若gateway那邊只有傳ACK(06)下來，代表gateway沒有資料需要給我
                # 若gateway那邊有傳資料給我，我就回ACK(06)給他
                if _data.split(',')[-1].split(":")[1][2:-1] != "06":
                    ####################################
                    # 封裝ACK並送回
                    # target = NODE_01
                    data = {"t": format( _data.split(',')[1].split(":")[1][2:-1] ),"id":self._id,"data":packer.ACK}
                    print("ACK:" + format( data ))
                    _length, _ack = packer.Pack_Str( json.dumps(data) )
      
                    ack = [int(hex(c), 0) for c in _ack]
            
                    print("ACK: {}, {}".format( self._id, ack))
                    self.write_payload(ack)
                    self.set_mode(MODE.TX)
                    ##################################
                # set TX
                self.rx_done = True
                # comment it will receive countinous
                self.set_dio_mapping([1,0,0,0,0,0])    # TX
                self.set_mode(MODE.STDBY)
                self.clear_irq_flags(TxDone=1)
            else:
                print("This packet is not your package!")
                on_tx_done()
        except:
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print("Non-hexadecimal digit found...")
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print("Receive: {}".format( data))
        


    def on_tx_done(self):
        print("\nTxDone")
        # set RX
        self.set_dio_mapping([0,0,0,0,0,0])    # RX
        sleep(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        self.clear_irq_flags(RxDone=1)
      

    def start(self):
        while True:
            print('----------------------------------')
            sleep(1)
            
            
            try:
                rawinput = raw_input(">>> ")
            except NameError:
                rawinput = input(">>> ")
            except KeyboardInterrupt:
                lora.set_mode(MODE.SLEEP)
                sleep(.5)
                BOARD.teardown()
                exit()
            
            targetNode = input("Send to:")
            #number = None
            #number = str(readNumber())

            if len(rawinput) < 200:
                # t:target d:data
                data = {"t":targetNode,"id":self._id,"d":rawinput}
                _length, _payload = packer.Pack_Str( json.dumps(data) )

                try:
                    # for python2
                    data = [int(hex(ord(c)), 0) for c in _payload]
                except:
                    # for python3 
                    data = [int(hex(c), 0) for c in _payload]

                for i in range(3):
                    if self.rx_done is True:
                        self.rx_done = False
                        break
                    else:
                        self.set_mode(MODE.SLEEP)
                        self.set_dio_mapping([1,0,0,0,0,0])    # TX
                        sleep(.5)
                        lora.set_pa_config(pa_select=1)
                        self.clear_irq_flags(TxDone=1)
                        self.set_mode(MODE.STDBY)
                        sleep(.5)
                        print("Raw TX: {}".format(data))

                        self.write_payload(data)
                        self.set_mode(MODE.TX)

                        ## ALOHA(1~3) ## on_tx_done
                        t = i*i + int(np.random.random() * float(_length))
                        print("ALOHA Waiting: {}".format( t))
                        sleep(t)


lora = LoRaBeacon()
lora.set_mode(MODE.STDBY)
lora.set_pa_config(pa_select=1)
lora.set_coding_rate(4)
lora.set_freq(868)
try:
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("")
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    sleep(.5)
    BOARD.teardown()
