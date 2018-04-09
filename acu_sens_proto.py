'''Grabs audio data from mic and sends to IoT Endpoint'''
#!/usr/bin/env python

from __future__ import print_function
import json, os, time, datetime
import boto3
#from modules import helpers as h
import pyaudio, wave

here = 'here'

BUFFER_SIZE = 1024
REC_SECONDS = 5
RATE = 48000
WAV_FILENAME = 'test'
FORMAT = pyaudio.paInt16

# define callback (2)
def recording_callback(in_data, frame_count, time_info, status):
    ### publish in_data to iot
    data = wf.readframes(frame_count)

    return (data, pyaudio.paContinue)

#init sound stream
pa = pyaudio.PyAudio()

for index in range(pa.get_device_count()): 
    desc = pa.get_device_info_by_index(index)
    print (desc)
    print (here,'1')
    if desc["name"] == "record":
        print ("DEVICE: %s  INDEX:  %s  RATE:  %s " %  (desc["name"],
                                                        index,
                                                        int(desc["defaultSampleRate"])))
        mic_index = index
        print (mic_index)
    try:
        print (here,'2')
        stream = pa.open(
            format = FORMAT,
            input = True,
            channels = 1,
            rate = RATE,
            input_device_index = int(mic_index),
            frames_per_buffer = BUFFER_SIZE,
            stream_callback = recording_callback)
        print (here, '3')
    except Exception as exc_err:
        ### publish exception message stating no recording device found
    except ValueError as val_err:
        ### publish exceptin message stating neither i/p nor o/p are set to TRUE

if stream:
    # start the stream (4)
    stream.start_stream()

    # wait for stream to finish (5)
    while stream.is_active():
        time.sleep(0.1)
    print (here, '4')
    # stop stream (6)
    stream.stop_stream()
    stream.close()
    wf.close()

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