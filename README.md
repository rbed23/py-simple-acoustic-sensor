# acoustic-sensor-prototype
---
## Description

Sets up secure audio streaming, sampling, processing, and publishing on a Raspberry Pi communicating over AWS IoT via MQTT protocol.

## Dependencies and Package Requirements

The following installations and imports are required to run this application.

__Installs__

1. **Python 2.7** via [python software foundation](https://www.python.org/downloads/)
2. **AWSIoTPythonSDK** via [aws-iot-device-sdk-python on github] (https://github.com/aws/aws-iot-device-sdk-python)
- allows developers to write Python script to access / control devices via the AWS IoT platform
2. **RPI Audio Levels** via [rpi-audio-levels on github] (https://github.com/colin-guyon/rpi-audio-levels)
- this script also uses the GPU FFT library installed on RPi (see [link](http://www.aholme.co.uk/GPU_FFT/Main.htm))

__Imports__

1. Pyaudio
2. Numpy
3. Queue
4. Threading
5. Cython (if installing RPI Audio Levels library, above)

__Security Credentials__

1. Certificate Authority (AWS) Certificate File
2. Private Key File
3. _Activated_ Certificate File

__Hardware Used__

1. Raspberry Pi 3 Model B
2. Snopy Rampage SN-RM7X USB Microphone

## Configuration

### _acu_sens_config.json_

__Keys__

- aws_vars (mandatory): necessary to connect to Hala AWS endpoint broker
- notes (not mandatory): used only to document troubleshooting to possible issues

__Values__

- '<clientId>' in *_topics replaces the <clientId> string with the actual 'clientId' key-value


### _acu_sens_prototype.py_

__ENVR VARS__

- callback: will the script use the pyaudio stream callback feature or not
- recording_flag: used if callback == True, start recording immediately at runtime or wait
- NUM_THREADS: if callback == True, indicate how many workers to create for processing streaming audio data
- REC_SECONDS: if callback != True, run the script for a number of seconds
- iot_config_json: /path/to/config.json string

__Pyaudio and FFT VARS__

- RATE: sample rate of the microphone in Hz
- DATA_SIZE: sets the sample size of the buffer (base 2 exponential --> 2^X)
- BUFFER_SIZE: actual number of samples in the buffer
- FORMAT: Pyaudio data format of samples
