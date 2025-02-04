# Simple Acoustic Sensor
---
## Description

Sets up secure audio streaming, sampling, processing, FF transformation, and publishing via MQTT protocol

## Dependencies and Package Requirements

The following installations and imports are required to run this application.

__Helpful Guides__

1. [AWS IoT Development Guide](https://docs.aws.amazon.com/iot/latest/developerguide/what-is-aws-iot.html): Describe the basic features and hierachy of AWS IoT
1. [Git Guide](https://www.atlassian.com/git/tutorials): Helpful Git commands

__Installs__

1. **Python 3.6** via [python software foundation](https://www.python.org/downloads/)
1. **AWSIoTPythonSDK** via [aws-iot-device-sdk-python on github](https://github.com/aws/aws-iot-device-sdk-python)
    - allows developers to access / control devices via the AWS IoT platform
1. ~~**RPI Audio Levels** via~~ [rpi-audio-levels on github](https://github.com/colin-guyon/rpi-audio-levels)
    - ~~this script also uses the GPU FFT library installed on RPi~~ (see [link](http://www.aholme.co.uk/GPU_FFT/Main.htm))

__Imports__

1. Pyaudio
2. Numpy
3. Queue
4. Threading
5. ~~Cython (if installing RPI Audio Levels library, above)~~

__Security Credentials__

1. Root Certificate Authority Certificate File
2. Private Key File
3. _Activated_ Certificate File

__Hardware Used__

1. Raspberry Pi 3 Model B
2. Snopy Rampage SN-RM7X USB Microphone

## Configuration

### _acu_sens_config.json_

__Keys__

- aws_vars (mandatory): necessary to connect to Hala AWS endpoint broker

__Values__

- `<clientId>` in "*_topics" keys gets replaced with the actual 'clientId' value


### _acu_sens_prototype.py_

__ENVR VARS__

- ~~callback: will the script use the pyaudio stream callback feature or not~~
- ~~recording_flag: used if callback == True, start recording immediately at runtime or wait~~
- NUM_THREADS: if callback == True, indicate how many workers to create for processing streaming audio data
- ~~REC_SECONDS: if callback != True, run the script for a number of seconds~~
- iot_config_json: /path/to/config.json

__Pyaudio and FFT VARS__

- RATE: sample rate of the microphone in Hz
- DATA_SIZE: sets the sample size of the buffer (base 2 exponential --> 2^X)
- BUFFER_SIZE: actual number of samples in the buffer
- FORMAT: Pyaudio data format of samples
