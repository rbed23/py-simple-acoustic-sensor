'''Contains useful modules for the Acoustic Sensors Prototype Device'''
# !/usr/bin/env python
from __future__ import print_function
import time


def get_mic_index(pa):
    '''
    Get the USB microphone sound card position

    <type pa> pyaudio portaudio object
    <desc pa> none

    <<type index>> int
    <<desc index>> location index of the default mic device

    <<type desc>> dict
    <<desc desc>> description of the indexed mic device
    '''
    try:
        for index in range(pa.get_device_count()):
            desc = pa.get_device_info_by_index(index)
            desc['sample_rate'] = int(desc['defaultSampleRate'])
            if desc["name"] == "default":
                print(f"Recording from:\n  DEVICE: {desc['name']}\n"
                      f"  INDEX: {index}\n"
                      f"  RATE: {desc['defaultSampleRate']}")
                return index, desc
    except UnboundLocalError as ubl_err:
        print(f"Local Error: could not find microphone\n{ubl_err}")
    except Exception as err:
        print(f"Exception Error: could not find microphone\n{err}")


def set_stream(pa, rate, buffer, paformat, mic, cb):
    '''
    Initialize and open portaudio stream

    <type pa> portaudio object
    <desc pa> from pyaudio module

    <type rate> int
    <desc rate> default mic sampling rate

    <type buffer> int
    <desc buffer> int should be power of 2

    <type format> portaudio sample format
    <desc format> paFloat32, paInt32, paInt24,
                  paInt16, paInt8, paUInt8, paCustomFormat

    <type mic> int
    <desc mic> microphone index location

    <type cb> str
    <desc cb> portaudio stream_callback function name

    <<type stream>> pyaudio portaudio wrapper object
    <<desc stream>> based on module arguments

    <<type ts>> float
    <<desc ts>> time.time() float response
    '''
    try:
        stream = pa.open(
            format=paformat,  # pyaudio data format ENVR VAR
            channels=1,       # defines a single channel
            input=True,       # defines channel as input
            rate=rate,        # USB mic sample rate
            input_device_index=mic,    # gets mic location
            frames_per_buffer=buffer,  # USB mic framerate
            stream_callback=cb)        # sets up callback f(x)
        ts = time.time()      # stream opened, lifetime begins
    except TypeError as typ_err:
        print(f"Type Error: {typ_err}")   # no recording device found
    except ValueError as val_err:
        print(f"Value Error: {val_err}")  # neither i/p nor o/p are set to TRUE
    except NameError as nam_err:
        print(f"Name Error: {nam_err}")
    except Exception as exc_err:
        print(f"Exception Error: {exc_err}")
    else:
        return stream, ts
