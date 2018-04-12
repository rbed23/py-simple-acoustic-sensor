'''Grabs audio data from mic and sends to IoT Endpoint'''
#!/usr/bin/env python

from __future__ import print_function
#basic import python libraries
import json, sys, time
import pyaudio, numpy as np, Queue, threading
from modules import helpers as h
from modules import iot_helpers as ioth
from modules import pyaudio_helpers as pyah

'''
ENVR VARIABLES
Used for configuring / formatting the prototype for testing and 
MQTT and USB mic configuration
'''
callback = True # will the script run streaming audio data
recording_flag = False # will the script start recording audio data at runtime
NUM_THREADS = 2 # number of worker threads to create for processing / publishing audio data
iot_configuration_json = '/opt/acoustic-sensor-prototype/acu_sens_config.json' 

RATE = 48000 # sample rate of the USB microphone
BUFFER_SIZE = 2048 # number of samples used to process at a time
FORMAT = pyaudio.paInt16 # pyaudio data format of samples
REC_SECONDS = 5 # IF callback != True, run audio stream viz for a length of time

# define callbacks
def audio_callback(in_data, frame_count, time_info, status):
    '''
    Streams audio data from input channel
    http://people.csail.mit.edu/hubert/pyaudio/docs/#example-callback-mode-audio-i-o
    for details
    '''
    if recording_flag == True:
        print ('recording...')
        audio_payload = {
            "id" : audio_iot_device['clientId'], # str obj
            "data" : np.fromstring(in_data, dtype=np.int16).tolist(), # list object
            "frame_count" : frame_count, # int object
            "time_info" :  time_info, # dict object
            "status" : status, # int object; status == 0 is good, 1/2 represents over-/under-flow
            "stream_started" : stream_opened_timestamp # float object
            }
	try:
            q.put(json.dumps(audio_payload)) # add payload to Queue
	except Queue.Full: # should never happen, since Queue size is infinite
	    print ("Queue is full")
	    create_workers() # just in case, will start draining Queue
    else:
    #       print ('streaming...')
        pass
    return (in_data, pyaudio.paContinue) # not used

# configure IoT device
audio_iot_device = ioth.setup_iot_device(iot_configuration_json)

# init IoT device client
audio_iot_client = ioth.get_iot_client(audio_iot_device)

# init sound stream
pa = pyaudio.PyAudio()

# itit audio buffer queue
q = Queue.Queue()

# connect to MQTT
audio_iot_client.connect(audio_iot_device['endpoint_url'], audio_iot_device['endpoint_port'])
audio_iot_client.loop_start()  

while not audio_iot_client.connected_flag and not audio_iot_client.bad_auth_flag:
    print ('waiting for connection...')
    time.sleep(2)
    if audio_iot_client.bad_auth_flag: 
        audio_iot_client.loop_stop()
        sys.exit()

# subscribe to channels to receive commands
ioth.subscriber_fx(audio_iot_client, audio_iot_device)

# configure pyaudio stream
mic_index = pyah.get_mic_index(pa)
if mic_index is not None:
    stream, stream_opened_timestamp = set_stream(RATE, BUFFER_SIZE, FORMAT, mic_index, audio_callback)

try:
    ### for handling streaming data    
    if callback:
        # start the stream (4)
        stream.start_stream()
        cnt = 0
        # wait for stream to finish (5)
        while stream.is_active():
            print ('--- ACTIVE STREAM ---')
            time.sleep(1.0)
            cnt += 1
            # switch between streaming/recording every 10 cnts
            if cnt == 10:
                recording_flag = True
            elif cnt == 20:
                recording_flag = False
                cnt = 0

            if not q.empty():
                h.create_workers(NUM_THREADS, q, audio_iot_device)
                print ("Size of Queue: " + str(q.qsize()))
                print ("Number of Threads: " + str(threading.activeCount()))
                print ("Enumerated Threads: " + str(threading.enumerate()))
    ### for displaying streaming data
    else:
        for i in range(int(REC_SECONDS*RATE/BUFFER_SIZE)): #go for a few seconds
            data = np.fromstring(stream.read(BUFFER_SIZE),dtype=np.int16)
            peak=np.average(np.abs(data))*2
            bars="#"*int(50*peak/2**16)
            print("%04d %05d %s"%(i,peak,bars))
except NameError as nam_err:
    print ("EXCEPTION: Name Error in main module: " + str(nam_err))
    h.close_application(pa, audio_iot_client)
except KeyboardInterrupt:
    h.close_application(pa, audio_iot_client, stream)

