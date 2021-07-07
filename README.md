# RFMGate
Bridge RFM69 Data visversa between a http requestor and a RFM69 mcu.

mcu actors:
- receive http values (nodeid: command), in a json-format
- foreward the command to the mcu (nodeid)
- store the acknowledge (the mcu state) in a json-format and send this back to the http requestor
- wait 300 ms before the next command can send

mcu sensor (unattended data):
- the mcu send values (like temperature etc.) unattended, perhaps in a interval
- the script store these values in a cached json-format (overwriting existing, older values)
- a http requestor can pull these data each time
