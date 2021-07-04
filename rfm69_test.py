# Simple example to send a message and then wait indefinitely for messages
# to be received.  This uses the default RadioHead compatible GFSK_Rb250_Fd250
# modulation and packet format for the radio.
# Author: Tony DiCola
import board
import busio
import digitalio
import adafruit_rfm69
import json

# Define radio parameters.
RADIO_FREQ_MHZ = 433.0  # Frequency of the radio in Mhz. Must match your
                        # module! Can be a value like 915.0, 433.0, etc.


# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
#CS = digitalio.DigitalInOut(board.D5)
#RESET = digitalio.DigitalInOut(board.D6)
# Or uncomment and instead use these if using a Feather M0 RFM69 board
# and the appropriate CircuitPython build:
#CS = digitalio.DigitalInOut(board.RFM69_CS)
CS = digitalio.DigitalInOut(board.CE1)
#RESET = digitalio.DigitalInOut(board.RFM69_RST)
RESET = digitalio.DigitalInOut(board.D25)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ)
header = rfm69.preamble_length #set to default length of RadioHead RFM69 library
# set node addresses
rfm69.node = 1
# Optionally set an encryption key (16 byte AES key). MUST match both
# on the transmitter and receiver (or be set to None to disable/the default).
rfm69.encryption_key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08'

# Print out some chip state:
print('Temperature: {0}C'.format(rfm69.temperature))
print('Frequency: {0}mhz'.format(rfm69.frequency_mhz))
print('Bit rate: {0}kbit/s'.format(rfm69.bitrate/1000))
print('Frequency deviation: {0}hz'.format(rfm69.frequency_deviation))

# Send a packet.  Note you can only send a packet up to 60 bytes in length.
# This is a limitation of the radio packet size, so if you need to send larger
# amounts of data you will need to break it into smaller send calls.  Each send
# call will wait for the previous one to finish before continuing.
#rfm69.send(bytes('Hello world!\r\n',"utf-8"))
# print('Sent hello world message!')


# Wait to receive packets.  Note that this library can't receive data at a fast
# rate, in fact it can only receive and process one 60 byte packet at a time.
# This means you should only use this for low bandwidth scenarios, like sending
# and receiving a single message at a time.
print('Waiting for packets...')
while True:
    #packet = rfm69.receive()
    packet = rfm69.receive(timeout=0.5, keep_listening=True, with_header=True)
    # Optionally change the receive timeout from its default of 0.5 seconds:
    #packet = rfm69.receive(timeout=5.0)
    # If no packet was received during the timeout then None is returned.
    if packet is None:
        continue
        # Packet has not been received
        print('Received nothing! Listening again...')
    else:
        # Received a packet!
        # Print out the raw bytes of the packet:
        print('RSSI: {0}'.format(rfm69.rssi))
        client_id = packet[1]
        print('data coming from: {0}'.format(client_id))
        # And decode to ASCII text and print it too.  Note that you always
        # receive raw bytes and need to convert to a text format like ASCII
        # if you intend to do string processing on your data.  Make sure the
        # sending side is sending ASCII data before you try to decode!
        del packet[0:4] # delete the header
        #packet_content = json.loads(packet)
        #packet_text = str(packet, 'ascii')
        my_json = packet.decode('utf8').replace("'", '"')
        print(my_json)
        #data = json.loads(my_json)
        #s = json.dumps(data, indent=4, sort_keys=True)
        #print(s)
        #print('Received (ASCII): {0}'.format(packet_text))
        #rfm69.send(bytes('Hello back again!\r\n',"utf-8"),timeout=2.0, tx_header=(client_id, 1, 0, 0))
