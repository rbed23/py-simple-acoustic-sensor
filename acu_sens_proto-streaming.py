'''Grabs audio data from mic and sends to IoT Endpoint'''

from __future__ import print_function

from modules import helpers as h
from modules import iot_helpers as ioth
from modules import pyaudio_helpers as pyah
import json
import numpy as np
import pyaudio
import queue as q
import time


'''
Global VARIABLES
Used for configuring / formatting the prototype for
MQTT, USB mic, and audio callback configurations
'''
# static script vars
NUM_THREADS = 2             # number of worker threads to create
iot_configuration_json = 'acu_sens_config.json'

# static FFT execution
DATA_SIZE = 11        # 10 = 1024 samples; 11 = 2048 samples; 12 = 4096 samples

# static PyAudio vars
RATE = 48000                # sample rate of the USB microphone
BUFFER_SIZE = 2**DATA_SIZE  # number of samples used to process at a time
FORMAT = pyaudio.paInt16    # pyaudio data format of samples

# audio callback functionality instantiations
q_process = q.Queue()  # for detecting/analyzing audio
q_analyze = q.Queue()  # FFT processing and publishing to IoT


# define callbacks
def audio_callback(in_data, frame_count, time_info, status):
    '''
    Streams audio data from input channel
    http://people.csail.mit.edu/hubert/pyaudio/docs/#example-callback-mode-audio-i-o
    for details
    '''
    audio_payload = {
        "raw_data": np.fromstring(in_data, dtype=np.int16).tolist(),
        "frame_count": frame_count,
        "sample_rate": RATE,
        "time_info": time_info,  # dict
        "status": status    # int object; status == 0 is good
                            # 1 is over-flow
                            # 2 is under-flow
        }

    # put audio payload data in worker queue to process
    try:
        global q_process
        q_process.put(json.loads(audio_payload))  # puts to Analyze Queue
    except q.Full:  # should never happen, since Queue size is infinite
        print("Queue is full")

    return (None, pyaudio.paContinue)


def main():
    # configure IoT device
    iot_device = ioth.setup_iot_device(iot_configuration_json)

    # init IoT device client
    iot_client = ioth.get_iot_client(iot_device)

    # init sound stream
    pa = pyaudio.PyAudio()

    # connect to MQTT
    iot_client.connect(iot_device['endpoint_url'], iot_device['endpoint_port'])

    iot_client.loop_start()
    while not iot_client.connected_flag and not iot_client.bad_auth_flag:
        print('waiting for connection...')
        time.sleep(2)
        if iot_client.bad_auth_flag:
            h.close_application(c=iot_client)

    # subscribe to channels to receive commands
    ioth.subscriber(iot_client, iot_device)

    # configure pyaudio stream
    mic_index, card_desc = pyah.get_mic_index(pa)

    # required by audio callback functionality providing sampling rate info
    global RATE
    # updates sampling rate to match microphone found
    if card_desc['sample_rate'] != RATE:
        RATE = card_desc['sample_rate']

    if mic_index is not None:
        stream, timestamp = pyah.set_stream(pa,
                                            card_desc['defaultSampleRate'],
                                            BUFFER_SIZE,
                                            FORMAT,
                                            mic_index,
                                            audio_callback)
        try:
            # start the stream (4)
            stream.start_stream()

            # wait for stream to finish (5)
            while stream.is_active():

                if not q_process.empty():  # if filled
                    h.create_workers(
                        q_process,
                        q_analyze,
                        NUM_THREADS)
                    if not q_analyze.empty():  # if filled
                        h.create_workers(
                            q_analyze,
                            NUM_THREADS,
                            iot_device,
                            iot_client)
                time.sleep(0.1)
                # audio_callback putting ADIs into Process Queue in real-time
                # every 100ms addl worker threads created to handle Q'd ADIs
        except NameError as nm_err:
            print(f"Error: Name Error in main module: {nm_err}")
            h.close_application(pa=pa, c=iot_client)
        except KeyboardInterrupt:
            h.close_application(pa=pa, c=iot_client, s=stream)
    else:
        print(f"Could not find a default mic configured, closing application")
        h.close_application(pa=pa, c=iot_client)


if __name__ == "__main__":
    main()
