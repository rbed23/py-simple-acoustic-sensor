'''Contains useful modules for the Acoustic Sensors Prototype Device'''
#!/usr/bin/env python
from __future__ import print_function
import time

def get_mic_index(pa):
    '''
    Get the USB microphone sound card position

    :type pa: pyaudio portaudio object
    :param pa: none
    '''
    try:
        for index in range(pa.get_device_count()): 
            desc = pa.get_device_info_by_index(index)
            if desc["name"] == "default":
                print ("DEVICE: %s  INDEX:  %s  RATE:  %s " %  (desc["name"],
                                                                index,
                                                                int(desc["defaultSampleRate"])))
                print ('Recording from device', index)
		print (json.dumps(desc, indent = 2))
                return index
    except UnboundLocalError as err:
        print ("Unbound Local Error: could not find microphone by indexing devices; " + str(err))
    except Exception as exc_err:
        print ("Exception Error: could not find microphone by indexing devices; " + str(type(exc_err) + str(exc_err)))

def set_stream(rate, buffer, paformat, mic, cb):
    '''
    Initialize and open portaudio stream

    :type rate: int
    :param rate: default mic sample rate

    :type buffer: int
    :param buffer: multiples of 1024

    :type format: portaudio sample format
    :param format: paFloat32, paInt32, paInt24, paInt16, paInt8, paUInt8, paCustomFormat

    :type mic: int
    :param mic: none

    :type cb: str
    :param: portaudio stream_callback function name

    :return:
    :type stream: pyaudio portaudio wrapper object
    :param stream: based on module arguments

    :type opened_ts: float
    :param opened_ts: time.time() float response
    '''
    try:
        stream = pa.open(
            format = paformat, # pyaudio data format ENVR VAR
            channels = 1, # defines a single channel
            input = True, # defines channel as input
            rate = rate, # USB mic sample rate
            input_device_index = mic, # gets mic location
            frames_per_buffer = buffer, # USB mic framerate
            stream_callback = cb) # sets up callback f(x)
        opened_ts = time.time() # stream opened, lifetime begins
    except TypeError as typ_err:
        print ("Type Error: " + str(typ_err)) # no recording device found
    except ValueError as val_err:
        print ("Value Error: " + str(val_err)) # neither i/p nor o/p are set to TRUE
    except NameError as nam_err:
        print ("Name Error: " + str(nam_err))
    except Exception as exc_err:
        print ("Exception Error: " + str(type(exc_err)), str(exc_err))
    else:
        return stream, opened_ts