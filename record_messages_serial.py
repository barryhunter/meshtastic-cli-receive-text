# This script compiles stats about received messages
# ... the output is intended to give some idea of what is being received and when
# ... shows how many of each type of message, as well as first and last received. Shows time between first and last as well as average time between messages.
# ... ... useful to see how often (for example) recieving position and telementry from noded
# ... Only counts messages since startup, no attempt to look at historic messages. (ie doesnt show older nodes, even tbhough in node list) 
# ... Last message is shown in Yellow
# ... Nodes last heard over 15 minutes ago, are shown in red. 
# ... display updated every time a message recieved

# It also writes a log of ALL messages to an 'extemded' rangetest.csv
# ... this should be mostly compatible with rangetest.csv saved from Android App
# ... although this file includes all messages, even ones sent by own node!
# ... also includes some EXTRA columns at the end, hopefully to make more useful. 
# ... in particular to include the hopstart (so can compute hops away!) and the rssi (others included just because can) 
# ... ... not implemented yet, but would like to have extended logging of NEIGHBOUR and TRACEROUTE packets, to enable enhanced mapping. 

# Note uses 'wakepy' in an attempt to keep the computer 'awake' so can continue to log unattended! (otherwise laptop might goto sleep for example) 
#  ... does not keep screen on, but that would be a one line change

# Press Ctrl-C to exit!


import time
import sys
from pubsub import pub
from meshtastic.serial_interface import SerialInterface
from meshtastic import portnums_pb2
import csv
from wakepy import keep
import math

serial_port = '/dev/ttyACM0'  # Replace with your Meshtastic device's serial port (on windows something like "COM5", on linux like '/dev/ttyACM0')
my_id = '' # you could put your node id (as !hex id) but typcailly it autodetected

# shouldnt need to to modify below (unless want to change behaviour) 
################################################################

node_info = {}
last = None
logfile = None
csvfile = None

################################################################

def get_node_info(serial_port):
    global node_info
    
    print("Initializing SerialInterface to get node info...")
    local = SerialInterface(serial_port)
    node_info = local.nodes
    local.close()
    print("Node info retrieved.")

################################################################

def on_receive(packet, interface):
    try:
        fromnum = packet['fromId']
        port = packet['decoded']['portnum'].replace('_APP', '')

        ######################################
        # compile per message stats

        global node_info, last
        last= time.time()

        node = node_info.setdefault(fromnum,{})
        
        stat = node.setdefault('stat', {})
        stat[port] = stat.get(port, 0) + 1
        
        node.setdefault('first', {}).setdefault(port, time.time())
        node.setdefault('last', {})[port] = time.time()
        
        node['lastHeard'] = last   #set by device in orginal nodelist, but we should update it each time!
        
        #todo - if NodeInfo packet, we should update 'user' list
        # - if Position packet, should update position (for our csv log) 

        if packet['decoded']['portnum'] == 'POSITION_APP':
            node['latitide']  = packet['decoded']['position']['latitude']
            node['longitude'] = packet['decoded']['position']['longitude']
            node['altitude'] = packet['decoded']['position']['altitude']
        
######################################
# wtite log entry
        
        mynode = node_info.get(my_id,{})
        
        logfile.writerow([
            time.strftime("%Y-%m-%d"), # todo use packet['time'] (if can be trusted!) 
            time.strftime("%H:%M:%S"),
            packet.get('from',''), #interger from
            node.get('user',{}).get('longName',''),
            node.get('latitide',''),
            node.get('longitude',''),
            mynode.get('latitide',''),
            mynode.get('longitude',''),
            mynode.get('altitude',''),
            packet.get('rxSnr',''),
            0, ##todo calc distance. should copy formular from client code. 
            packet.get('hopLimit',''),
            packet['decoded']['payload'].decode('utf-8') if packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP' else f"<{packet['decoded']['portnum']}>",
            ## extended columns!
            node.get('user',{}).get('shortName',''),
            packet.get('to',''),
            packet.get('id',''),
            packet.get('channel',''),
            packet.get('hopStart',''),
            packet.get('rxRssi','')
            ])
            # todo, is to decode some other types of packets - partucylly neigbour and traceroute?
        csvfile.flush()

######################################
# print all nodes stats

        print("----------------------------------")
        print()
        
        for fromnum, node in node_info.items():
            # only look at nodes we have compiled stats for
            if 'stat' in node:
                shortname = node.get('user',{}).get('shortName','Unk')
                longname = node.get('user',{}).get('longName','Unknown')

                if node['lastHeard'] < (time.time() - 60*15):
                    print("\033[0;31m", end="") #red
                
                ## todo print snr/rssi or hops-away if have them
                print(f"{fromnum}: {shortname:4}: ({longname})")
                for port, count in node['stat'].items():
                    start = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(node['first'][port]))
                    colored = False
                    if math.floor(node['last'][port]) == math.floor(last): #could check port too, but maybe nice if highlight all if gets lots in same second?
                        colored = True
                        print("\033[1;33m",end="") # yellow

                    if count > 1:
                        end = time.strftime("%H:%M:%S", time.localtime(node['last'][port]))
                        diff = node['last'][port] - node['first'][port]
                        avg = diff / (count - 1)
                        print(f"  {port:12} x{count:3d}  {start} > {end} = {diff:7.1f} seconds  ({avg:5.1f} avg)")
                    else:
                        print(f"  {port:12} x{count:3d}  {start}")
                    if colored:
                        print("\033[0m",end="") # white
                
                print("\033[0m") #white
        print()

######################################
        
    ##except KeyError:
    ##    pass  # Ignore KeyError silently
    except UnicodeDecodeError:
        pass  # Ignore UnicodeDecodeError silently

################################################################

def main():
    global csvfile, logfile, my_id
    
    print(f"Using serial port: {serial_port}")

    # Retrieve and parse node information
    get_node_info(serial_port)

    # Get our own node identity from the list
    for fromnum, node in node_info.items():
        if 'isFavorite' in node:
            my_id = fromnum

    with keep.running() as m:
    ##with keep.presenting() as m: ##todo, use instead, if alway want to keep the screen on!
        print('active_method:', m.active_method, ' (keeps computer awake!)')
        #print('used_method:', m.used_method)

        # setup writing to CSV file
        csvfile = open('rangetest.csv', 'a', newline='') 
        logfile = csv.writer(csvfile)
        if csvfile.tell() == 0:
            logfile.writerow(["date","time","from","sender name","sender lat","sender long","rx lat","rx long","rx elevation","rx snr","distance","hop limit","payload",
                              "sender","to","id","channel","hop start","rs rssi","extended payload"])

        # Subscribe the callback function to message reception
        pub.subscribe(on_receive, "meshtastic.receive")
        print("Subscribed to meshtastic.receive")

        # Set up the SerialInterface for message listening
        local = SerialInterface(serial_port)
        print("SerialInterface setup for listening.")

        # Keep the script running to listen for messages
        try:
            while True:
                if last:
                    diff = time.time() - last
                    print(f"\033[1;33m({diff:.0f} seconds ago)\033[0m", end="\r")
                sys.stdout.flush()
                
                time.sleep(3)  # Sleep to reduce CPU usage
        except KeyboardInterrupt:
            print("Script terminated by user")
            local.close()

if __name__ == "__main__":
    main()
