#!/usr/bin/env python3
# -*- coding: utf8 -*-
""" A simple continuous receiver class. """
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
import time
import json
import packer
import sys 
import numpy as np
sys.path.insert(0, '../')
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from SX127x.LoRaArgumentParser import LoRaArgumentParser

import paho.mqtt.client as mqtt

BOARD.setup()

parser = LoRaArgumentParser("Continous LoRa receiver.")
host = "iot.cht.com.tw"
topic="/v1/device/30561198196/rawdata"
user, password = "PKEHX2UCCYP2GTGRZH", "DKRTWZ25KX9F45SPUA"

client = mqtt.Client()
client.username_pw_set(user, password)
client.connect(host, 1883, 60)

# python2
try:
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

class LoRaRcvCont(LoRa):
    storage = [None,None]
    
    def __init__(self, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0,0,0,0,0,0])    # RX
        self._id = "GW_01"

    def on_rx_done(self):
        print("\nRxDone")
        print('----------------------------------')

        payload = self.read_payload(nocheck=True)
        data = ''.join([chr(c) for c in payload])

        try: 
            _length, _data = packer.Unpack_Str(data)
            print("Error = 1")
            # 判斷是否為自己的封包
            if _data.split(',')[0].split(":")[1][2:-1] == self._id:
              print("Time: {}".format( str(time.ctime() )))
              print("Length: {}".format( _length ))
              print("Raw RX: {}".format( payload ))
              
              try:
                # python3 unicode
                print("Receive: {}".format( _data.encode('latin-1').decode('unicode_escape')))
              except:
                # python2
                print("Receive: {}".format( _data ))
              ####################################
              # 封裝ACK並送回
              # target = NODE_01
              # 如果當前target的storage不為空，代表這個GW有資料要傳給他
              # 如果GW送來的，或是Node送來但是storage沒東西
              print(_data.split(',')[1].split(":")[1][2:-1].split('_')[0])
              index=int(_data.split(',')[1].split(":")[1][2:-1].split('_')[1])
              print("123")
              if _data.split(',')[1].split(":")[1][2:-1].split('_')[0] == "GW" or (_data.split(',')[1].split(":")[1][2:-1].split('_')[0] == "NODE" and self.storage[int(_data.split(',')[1].split(":")[1][2:-1].split('_')[1])] == None):
                  print("Send by GW or (send by node and storage is empty)")
                  data = {"t": format( _data.split(',')[1].split(":")[1][2:-1] ),"id":self._id,"data":packer.ACK}
              # 如果是Node送來，而且裡面的是data不是ACK，重送storage裡面的東西
              elif _data.split(',')[2].split(":")[1][2:-1] != "06" and _data.split(',')[1].split(":")[1][2:-1].split('_')[0] == "NODE":
                  print("Receive data but storage is not empty")
                  data = {"t": format( _data.split(',')[1].split(":")[1][2:-1] ),"id":self._id,"data":self.storage[int(_data.split(',')[1].split(":")[1][2:-1].split('_')[1])]}
              # 如果是Node送來，而且裡面的是ACK，則清空storage
              elif _data.split(',')[2].split(":")[1][2:-1] == "06" and _data.split(',')[1].split(":")[1][2:-1].split('_')[0] == "NODE":
                  print("Receive ACK")
                  self.storage[int(_data.split(',')[1].split(":")[1][2:-1].split('_')[1])] = None
              else:
                  print("ERROR")
              print("ACK" + format( data ))
              _length, _ack = packer.Pack_Str( json.dumps(data) )

              ack = [int(hex(c), 0) for c in _ack]
      
              print("ACK: {}, {}".format( self._id, ack))
              self.write_payload(ack)
              self.set_mode(MODE.TX)
              ##################################
              
              
              # 輸入下一個gateway(或RX)並送出
              targetNode = input("Send to:")
              # 如果目的地是GW，直接送出
              if targetNode.split('_')[0] == "GW":
                  data = _data.split('"')[-2]
                  
                  if len(data) < 200:
                    # t:target d:data
                    data = {"t":targetNode,"id":self._id,"d":data}
                    _length, _payload = packer.Pack_Str( json.dumps(data) )
    
                    try:
                        # for python2
                        data = [int(hex(ord(c)), 0) for c in _payload]
                    except:
                        # for python3 
                        data = [int(hex(c), 0) for c in _payload]
    
                    # set TX
                    self.rx_done = False
                    # forward data
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
                    self.reset_ptr_rx()
                    self.set_mode(MODE.RXCONT)
              # 如果目的地是Node，放進storage
              else:
                  print("Debug = 1:")
                  index = targetNode.split('_')[1]
                  print("Debug = 2,index = " + index)
                  self.storage[int(index)] = _data.split('"')[-2]
                  print("Save " + _data.split('"')[-2] + " into storage:" + index + ":" + str(self.storage[int(index)]))
                  self.set_dio_mapping([0,0,0,0,0,0])    # RX
                  self.set_mode(MODE.STDBY)
                  sleep(1)
                  self.reset_ptr_rx()
                  self.set_mode(MODE.RXCONT)
                  self.clear_irq_flags(RxDone=1)
            else:
                print("This packet is not your package!")
                print("\nTxDone")
                self.set_dio_mapping([0,0,0,0,0,0])    # RX
                self.set_mode(MODE.STDBY)
                sleep(1)
                self.reset_ptr_rx()
                self.set_mode(MODE.RXCONT)
                self.clear_irq_flags(RxDone=1)

        except:
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print("Non-hexadecimal digit found...")
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print("Receive: {}".format( data))

    def on_tx_done(self):
        print("\nTxDone")
        self.set_dio_mapping([0,0,0,0,0,0])    # RX
        self.set_mode(MODE.STDBY)
        sleep(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        self.clear_irq_flags(RxDone=1)


    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(1)
            rssi_value = self.get_rssi_value()
            status = self.get_modem_status()
            #sys.stdout.flush()
            #sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))

            """
            try:
                #input = raw_input
                rawinput = raw_input(">>> ")
            except NameError:
                rawinput = input(">>> ")
            except KeyboardInterrupt:
                lora.set_mode(MODE.SLEEP)
                sleep(.5)
                BOARD.teardown()
                exit()
            """




lora = LoRaRcvCont(verbose=False)
args = parser.parse_args(lora)
lora.set_mode(MODE.STDBY)
lora.set_pa_config(pa_select=1)
lora.set_coding_rate(4)
lora.set_freq(868)
try:
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    sleep(.5)
    BOARD.teardown()
