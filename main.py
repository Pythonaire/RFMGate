#!/usr/bin/env python3
import board, busio, digitalio, rfm69_driver
import logging, json, socket, time, signal, sys, threading
import RPi.GPIO as io
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

file = open("RFM69.json","r")
RFM69Devices = json.load(file)
file.close()
# {"10": "None", "11": "None": "12": None}
for x, y in RFM69Devices.items(): # convert to python None for easier handling
    y = None

app = Flask(__name__)
@app.route('/setValue', methods=['POST', 'GET'])
def setValue():
    global RFM69Devices
    try:
        data = json.loads(request.get_json())
        keys = list(data)
        to_node = list(keys)[0]
        cmd = data[to_node]
        RFM69Devices[to_node] = None
        Transceiver.mcu_send(to_node, cmd)
        res = json.dumps({key: RFM69Devices[key] for key in RFM69Devices.keys() & {to_node}})
        if RFM69Devices[to_node] == None: # not reached
             res = json.dumps({to_node:'None'})
             logging.info('**** no response from {}'.format(res))
        return res
    except socket.error as e:
        logging.info('**** socket exception: {}'.format(e))
    

@app.route('/cached', methods=['POST', 'GET'])
def cached():
    global RFM69Devices
    try:
        data = json.loads(request.get_json())
        keys = list(data)
        node = list(keys)[0]
        res = json.dumps({key: RFM69Devices[key] for key in RFM69Devices.keys() & {node}})
        return res
    except Exception as e:
        logging.info('**** socket exception: {}'.format(e))
    
class RFMTransceiver():
    RADIO_FREQ_MHZ = 433.0
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    rfm69 = rfm69_driver.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000)
    rfm69.tx_power= 18 # for RFM69HCW can by set between -2 and 20
    header = rfm69.preamble_length #set to default length of RadioHead RFM69 library
    # Optionally set an encryption key (16 byte AES key). MUST match both
    # on the transmitter and receiver (or be set to None to disable/the default).
    rfm69.encryption_key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08'
    dio0_pin = 24 # Pin connected to the RFM69 chip DIO0
    NODE = 1 # RFM69 bridge node id

    def __init__(self):
        io.setmode(io.BCM)
        io.setup(self.dio0_pin, io.IN,pull_up_down=io.PUD_DOWN) # set dio0 on GROUND as default

    def start_listen(self): # start DIO detection for reading
        self.rfm69.listen()
        io.add_event_detect(self.dio0_pin, io.RISING, callback = self.mcu_recv)

    def stop_listen(self):
        io.remove_event_detect(self.dio0_pin)

    def mcu_send(self, to_node, cmd):
        global RFM69Devices
        value = bytes("{}".format(cmd),"UTF-8")
        self.stop_listen() 
        #logging.info("**** send command {0} to node {1} ****".format(cmd, to_node))
        self.rfm69.send(value, int(to_node), self.NODE, 0, 0)
        self.start_listen()
        time.sleep(0.3) # 100 ms set on mcu


    def mcu_recv(self, irq):
        global RFM69Devices
        data = self.rfm69.receive(keep_listening= True, rx_filter=self.NODE)
        if data != None:
            from_node = data[1] # header information "from"
            payload = data[4:]
            rfm_data = json.loads(payload.decode('utf8').replace("'", '"')) # replace ' with " because of json handling in C++
            logging.info('*** from: {0} with RSSI: {1} got : {2}'.format(from_node, self.rfm69.last_rssi, rfm_data))
            # rfm_data : {'node':{key:value,key:value,...}}, caution ! node is a string, because of json definition
            RFM69Devices[str(from_node)] = rfm_data[str(from_node)]

def signal_handler(signal, frame):
    logging.info('Signal handler called with signal', signal)
    try:
        io.cleanup()
        FlaskProcess.join()
        sys.exit(0)
    except Exception as e:
        logging.info("Could not stop Flask because of error: %s", e)
        raise
            
if __name__ == '__main__':
    Transceiver = RFMTransceiver()
    Transceiver.start_listen()
    FlaskProcess = threading.Thread(target=app.run(debug=False, port=8001, host='0.0.0.0'))
    FlaskProcess.daemon = True
    FlaskProcess.start()
    signal.signal(signal.SIGTERM, signal_handler)
    