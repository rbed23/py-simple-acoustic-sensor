'''Grabs audio data from mic and sends to IoT Endpoint'''
#!/usr/bin/env python

from __future__ import print_function
#basic import python libraries
import json, os, time, sys, ssl
import pyaudio, numpy as np, Queue, threading
from modules import helpers as h
from modules import iot_helpers as ioth
from modules import pyaudio_helpers as pyah

# Import AWSIoTSDK package
#from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.core.protocol.paho import client as mqtt

callback = True
recording_flag = False
buffer_dump_size = 5
num_threads = 2
iot_configuration = '/opt/acoustic-sensor-prototype/acu_sens_config.json'

BUFFER_SIZE = 1024
REC_SECONDS = 5
RATE = 48000
WAV_FILENAME = 'test'
FORMAT = pyaudio.paInt16

np.set_printoptions(threshold=1000)

# define IoT worker
def iot_queue_worker(q, pub_channel):
    while True:
        try:
            item = q.get_nowait()
            if item is None:
                print ("Item returned 'None' from Queue")
                break
        except Queue.Empty:
            print ("Queue is empty")
            break
        else:
            print ('publishing...')
            audio_iot_client.publish(pub_channel, item, 1)
            q.task_done()

def create_workers(nthreads, q, device):
    thrdcnt = 1
    for i in range(nthreads):
        worker = threading.Thread(target=iot_queue_worker, args=(q,ioth.update_pub_channel(device)))
        worker.setDaemon(True)
        worker.start()
        print ('Started worker thread-' + str(thrdcnt))
        thrdcnt += 1

# define callbacks
def audio_callback(in_data, frame_count, time_info, status):
    # building buffer
    if recording_flag == True:
        print ('recording...')
        audio_payload = {
            "id" : audio_iot_device['clientId'],
            "data" : np.fromstring(in_data, dtype=np.int16).tolist(),
            "frame_count" : frame_count,
            "time_info" :  time_info,
            "status" : status,
            "stream_started" : stream_time_opened
            }
	try:
            q.put(json.dumps(audio_payload))
	except Queue.Full:
	    print ("Queue is full")
	    create_workers()
    else:
#        print ('streaming...')
	pass
    return (in_data, pyaudio.paContinue)

# configure IoT device client
audio_iot_device = ioth.setup_iot_device(iot_configuration)

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

ioth.subscriber_fx(audio_iot_client, audio_iot_device)

# configure pyaudio stream
mic_index = pyah.get_mic_index(pa)

if mic_index is not None:
    try:
        stream = pa.open(
            format = FORMAT,
            input = True,
            channels = 1,
            rate = RATE,
            input_device_index = int(mic_index),
            frames_per_buffer = BUFFER_SIZE,
            stream_callback = audio_callback)
        stream_time_opened = time.time()
    except TypeError as typ_err:
        print ("Type Error: " + str(typ_err))
    ### publish exception message stating no recording device found
    except ValueError as val_err:
        print ("Value Error: " + str(val_err))
    ### publish exceptin message stating neither i/p nor o/p are set to TRUE
    except NameError as nam_err:
        print ("Name Error: " + str(nam_err))
    except Exception as exc_err:
        print ("Exception Error: " + str(type(exc_err)), str(exc_err))

try:
    ### for handling streaming data    
    if callback:
        # start the stream (4)
        stream.start_stream()
        cnt = 0
        thrdcnt = 1
        # wait for stream to finish (5)
        while stream.is_active():
            print ('--- ACTIVE STREAM ---')
            time.sleep(1.0)
            cnt += 1
            if cnt == 10:
                recording_flag = True
            elif cnt == 20:
                recording_flag = False
                cnt = 0

            if not q.empty():
		create_workers(num_threads, q, audio_iot_device)
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
    print ("Name Error: " + str(nam_err))
    # stop Pyaudio (7)
    pa.terminate()
    # stop IoT
    audio_iot_client.loop_stop()
    audio_iot_client.disconnect()
except KeyboardInterrupt:
    # stop stream (6)
    stream.stop_stream()
    stream.close()
    # stop Pyaudio (7)
    pa.terminate()
    # stop IoT
    audio_iot_client.loop_stop()
    audio_iot_client.disconnect()
