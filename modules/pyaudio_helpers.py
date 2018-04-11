'''Contains useful modules for the Acoustic Sensors Prototype Device'''
#!/usr/bin/env python
from __future__ import print_function
import json, random, string
import time, datetime

def get_mic_index(pyaudio_pa):
    try:
        for index in range(pyaudio_pa.get_device_count()): 
            desc = pyaudio_pa.get_device_info_by_index(index)
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
