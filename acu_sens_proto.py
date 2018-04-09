'''Grabs audio data from mic and sends to IoT Endpoint'''
#!/usr/bin/env python

from __future__ import print_function
import json, os, time, datetime
import boto3
#from modules import helpers as h
import pyaudio, wave
import numpy as np

callback = True
sending_flag = False

BUFFER_SIZE = 8000
REC_SECONDS = 5
RATE = 48000
WAV_FILENAME = 'test'
FORMAT = pyaudio.paInt16

np.set_printoptions(threshold=1000)

# define callbacks
def audio_callback(in_data, frame_count, time_info, status):
#    print ('inside callback:', str(sending_flag))
    if sending_flag == True:
        global audio_iot_client
        audio_payload = {
            "data" : np.fromstring(in_data, dtype=np.int16).tolist(),
	    "frame_count" : frame_count,
	    "time_info" :  time_info,
	    "status" : status,
	    "stream_started" : stream_time_opened
	    }
	print ('publishing...')
#        print (json.dumps(audio_payload, indent=2))
#        audio_iot_client.publish('hala/syria/sensors/audio/test1',json.dumps(audio_payload),1)
    return (in_data, pyaudio.paContinue)

#init sound stream
pa = pyaudio.PyAudio()

for index in range(pa.get_device_count()): 
    desc = pa.get_device_info_by_index(index)
    if desc["name"] == "default":
        print ("DEVICE: %s  INDEX:  %s  RATE:  %s " %  (desc["name"],
                                                        index,
                                                        int(desc["defaultSampleRate"])))
        mic_index = index
        print (mic_index)
    try:
        stream = pa.open(
            format = FORMAT,
            input = True,
            channels = 1,
            rate = RATE,
            input_device_index = int(mic_index),
            frames_per_buffer = BUFFER_SIZE,
	    stream_callback = audio_callback)

	print ('recording from device', mic_index, '(' + json.dumps(desc) + ')')
	stream_time_opened = time.time()

    except Exception as exc_err:
        print (str(exc_err))
	### publish exception message stating no recording device found
    except ValueError as val_err:
        print (str(val_err))
	### publish exceptin message stating neither i/p nor o/p are set to TRUE


### for displaying streaming data
'''
if not callback:
    for i in range(int(10*44100/1024)): #go for a few seconds
        data = np.fromstring(stream.read(BUFFER_SIZE),dtype=np.int16)
        peak=np.average(np.abs(data))*2
        bars="#"*int(50*peak/2**16)
        print("%04d %05d %s"%(i,peak,bars))
'''
if callback:
    # start the stream (4)
    try:
	stream.start_stream()
        cnt = 0
        # wait for stream to finish (5)
        while stream.is_active():
           print ('streaming...')
	   time.sleep(0.5)
	   cnt += 1
	   if cnt == 10:
	       sending_flag = True
	   elif cnt == 20:
	       sending_flag = False
	       cnt = 0
    except KeyboardInterrupt:
	# stop stream (6)
        stream.stop_stream()
        stream.close()

    # close PyAudio (7)
    pa.terminate()

#run recording
if stream:
    print('Recording...')
    data_frames = []
    for f in range(0, RATE/BUFFER_SIZE * REC_SECONDS):
        data = stream.read(BUFFER_SIZE)
        data_frames.append(data)
    print('Finished recording...')
    stream.stop_stream()
    stream.close()
    pa.terminate()
