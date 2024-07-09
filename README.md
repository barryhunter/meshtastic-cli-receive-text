# meshtastic-cli-receive-text
A python command line script to receive messages from Meshtastic. Run the read_messages.py script, and it will connect to your radio and display any text messages received by your node, on any channel, including private/direct messages.

I built this because this functionality is not available using the Meshtastic CLI (as of time of publishing).

# Installation
* git clone https://github.com/brad28b/meshtastic-cli-receive-text.git
* cd meshtastic-cli-receive-text
* pip3 install -r requirements.txt

# Usage
* Firstly, decide if you will be connecting to your node via serial or via TCP. If using serial, edit read_messages_serial.py and set the serial port for your device (usually /dev/ttyUSB0 or /dev/ttyACM0). If using TCP, edit read_messages_tcp.py and set the IP address of your node.
* Then to run the script:
* For Serial: python read_messages_serial.py
* For TCP: python read_messages_tcp.py

* To exit, use Ctrl-C

![Screenshot 2024-07-08 115255](https://github.com/brad28b/meshtastic-cli-receive-text/assets/70585927/9df01ec8-a774-4f64-80d1-b040e9d57181)

