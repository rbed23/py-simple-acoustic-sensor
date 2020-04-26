'''Contains useful modules for the Acoustic Sensors Prototype Device'''
# !/usr/bin/env python
from __future__ import print_function
from modules import iot_helpers as ioth
import numpy as np
import json
import queue
import sys
import threading


def audio_analysis_detect(audio_item):
    '''
    Analyze audio data item to detect and flag to publish

    :type audio_item: str
    :param audio_item: raw, pyaudio-formatted, audio data samples

    :return:
    :type analyzed_item: TBD
    :param analyzed_item: TBD
    '''
    publish = False

    # do something here to detect interest in FFT response
    # set publish to True
    publish = True
    if publish:
        return audio_item
    else:
        return None


def audio_transformation(adi):
    '''
    Normalized and Transformed audio data item (adi)

    <type adi: dict
    <desc adi: json formatted raw, pyaudio-formatted, audio data samples

    <<type tformed_adi>> dict
    <<desc tformed_adi>> processed pyaudio data item
    '''
    tformed_adi = adi
    raw_data = tformed_adi['raw_data']
    frame_cnt = tformed_adi['frame_count']
    sample_rate = tformed_adi['sample_rate ']

    '''Below grabbed from this site: https://plot.ly/matplotlib/fft/'''

    # setup fft vars
    tformed_adi['sample_time_ms'] = frame_cnt / sample_rate * 1000
    np_data = np.array(raw_data, dtype=np.int16)
    signal_len = len(np_data)
    num_samples_sec = sample_rate / frame_cnt

    # get Nyquist freq range (also F / 2)
    frqs = np.arange(frame_cnt)
    freq_range = frqs[range(signal_len / 2)] * num_samples_sec

    # get FFT coefficient data and normalize
    fftdata = np.fft.rfft(np_data) / signal_len
    fftdata_abs = np.abs(fftdata)
    tformed_adi['fft_data'] = np.array(fftdata_abs).tolist()
    tformed_adi['max_idx'] = int(np.argmax(fftdata_abs))
    tformed_adi['max_freq'] = np.argmax(fftdata_abs) * num_samples_sec
    tformed_adi['max_freq_idx'] = freq_range[tformed_adi['max_idx']]

    return tformed_adi


def create_workers(q_get, q_put, nthreads=1, device=None, client=None):
    '''
    Create threads to work on job(s)

    <type q_get> Queue object
    <desc q_get> non-empty queue

    <type q_put> Queue object
    <desc q_put> non-full queue

    <type nthreads> int
    <desc nthreads> number of threads being created

    <type device> dict
    <desc device> detailed device configuration

    <type client> AWS IoT Client
    <desc client> none
    '''
    for i in range(nthreads):
        if device is None and client is None:
            # process data and put into analysis Q
            worker = threading.Thread(
                        target=queue_worker_fft_process,
                        args=(q_get, q_put)
                        )
        else:
            # analyze data and publish
            worker = threading.Thread(
                        target=queue_worker_fft_analyze,
                        args=(q_get,
                              device,
                              client)
                        )
        worker.setDaemon(True)  # daemon ends thread at end of job
        worker.start()  # start worker on job
        print('Started worker for thread...')


# defines analyzer worker job
def queue_worker_fft_process(q1, q2):
    '''
    Worker threads execute within this function

    <type q1> Queue object
    <desc q1> queue to take input

    <type q2> Queue object
    <desc q2> queue to put results
    '''
    while True:
        try:
            item = q1.get_nowait()
            if item is None:
                print("Item returned 'None' from Queue")
        except queue.Empty as empty_q:
            print(f"Queue is empty\n{empty_q}")
        else:
            print('processing...')
            q2.put(audio_transformation(item))  # fft of audio data
        finally:
            q2.task_done()
            q1.task_done()


# define IoT worker job
def queue_worker_fft_analyze(q, device, client):
    '''
    Worker threads execute within this function

    <type q> Queue object
    <desc q> infinite-sized Queue (maxsize = 0)

    <type device> dict
    <desc device> detailed device configuration

    <type client> AWS IoT Client
    <desc client> none
    '''
    while True:
        try:
            item = q.get_nowait()
            if item is None:
                print("Item returned 'None' from Queue")
        except queue.Empty as empty_q:
            print(f"Queue is empty\n{empty_q}")
        else:
            print('analyzing...')
            if audio_analysis_detect(item):  # if analysis meets threshold TBD
                print('publishing...')
                print(json.dumps(item, indent=2))
                for each in device['channels']:
                    client.publish(
                        ioth.update_channel(json.dumps(each),
                                            device['client_id']),
                        item,
                        1)
        finally:
            q.task_done()


def close_application(pa=False, c=False, s=False):
    '''
    Gracefully stop and close all open object(s) and client(s)

    <type pa> pyaudio portaudio object
    <type c> AWS IoT Client
    <type s> pyaudio portaudio object wrapper
    '''
    print('Closing application...')
    if s:
        print('Stopping and closing stream...')
        s.stop_stream()
        s.close()
    if pa:
        print("Terminating Pyaudio object...")
        pa.terminate()
    if c:
        print("Stopping loop and disconnecting MQTT client...")
        c.loop_stop()
        c.disconnect()
    print('Application CLOSED')
    sys.exit()
