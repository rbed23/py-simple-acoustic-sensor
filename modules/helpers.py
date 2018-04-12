'''Contains useful modules for the Acoustic Sensors Prototype Device'''
#!/usr/bin/env python
from __future__ import print_function
import json, random, string, base64, time
import threading, Queue
from modules import iot_helpers as ioth

def audio_processing(adi):
    '''
    Process and normalize audio data item
    :type adi: list
    :param adi: raw, pyaudio-formatted, audio data samples

    :return:
    :type padi: list
    :param padi: processed pyaudio data item
    '''
    padi = adi
    return padi

# create worker threads
def create_workers(nthreads, q, device, client):
    '''
    Create threads to work on job(s)

    :type nthreads: int
    :param nthreads: none

    :type q: Queue object
    :param q: infinite-sized Queue (maxsize = 0)

    :type device: dict
    :param device: device['clientId'] must exist

    :type client: AWS IoT client instance
    :param client: none
    '''
    for i in range(nthreads):
        # assign worker to execute iot_queue_worker job
        worker = threading.Thread(
                    target = iot_queue_worker, args = (
                                                    client,
                                                    q,
                                                    ioth.update_channel(
                                                        device['out_channel'],
                                                        device['clientId'])))
        worker.setDaemon(True) # daemon ends thread at end of job
        worker.start() # start worker on job
        print ('Started worker thread...')

# define IoT worker job
def iot_queue_worker(client, q, channel):
    '''
    Worker threads execute within this function

    :type client: AWS IoT client instance
    :param client: none

    :type q: Queue object
    :param q: infinite-sized Queue (maxsize = 0)

    :type channel: str
    :param channel: valid AWS IoT topic string
    '''
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
            print ('processing...')
            processed_item = audio_processing(item) # placeholder function, does nothing now
            print ('publishing...')
            client.publish(channel, processed_item, 1)
            q.task_done()

def close_application(pa=False, iot_client=False, stream=False):
    '''
    Gracefully stop and close all open object(s) and client(s)

    :type pa: pyaudio portaudio object
    :type iot_client: AWS IoT paho client
    :type stream: pyaudio portaudio object wrapper
    '''
    print ('Closing application...')
    if stream:
        print ('Stopping and closing stream...')
        stream.stop_stream()
        stream.close()
    if pa:
        print ("Terminating Pyaudio object...")
        pa.terminate()
    if iot_client:
        print ("Stopping loop and disconnecting MQTT client...")
        iot_client.loop_stop()
        iot_client.disconnect()
    print ('Application CLOSED')

def create_stream_event_envelope(payload,source_id,event_type,lambda_uid):
    '''
    Place data into envelope and address the package for Stream

    :type payload: dict object
    :param payload: data in the following format
    {
        "latitude" : float<degrees>,
        "altitude" : float<feet>,
        "longitude": float<degrees>,
        "flight_hex"   : str<hex code>,
        "flight_number"   : str<flight number>,
        "polled_timestamp" : float<timestamp>
    }

    :return:
    :type envelope: dict object
    :params envelope: envelope in the following format
    {
        "pkey"       : str<pkey>,
        "createtime" : int<createtime>,
        "src"        : str<source_id>,
        "type"       : str<event_type>,
        "data"       : dict<payload>
    }
    '''
    createtime = int(round(time.time()*1000))
    object_hash = hash(json.dumps(payload));
    event_id = source_id+'-'+lambda_uid+'-'+str(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)))
    partitionKey = ':'.join(map(str,[createtime, event_type, event_id, object_hash]))
    envelope = {
        "pkey"       : partitionKey,
        "createtime" : createtime,
        "src"        : source_id,
        "type"       : event_type,
        "data"       : payload
    }
    return envelope

def kinesis_put(client,data,stream_name,partition_key):
    '''
    Setup and put provided data into the stream

    :type client: class Kinesis Client
    :param client: valid Kinesis client object

    :type data: str
    :param data: data from json.dumps() call

    :type stream_name: str
    :param stream_name: name of the put stream

    :type partition_key: str
    :param partition_key: partition key assigned to a specific stream shard
    '''
    try:
        response = client.put_record(
            StreamName=stream_name,
            Data=data,
            PartitionKey=partition_key)
        print('Added data to new record in stream:',stream_name,'partition key:',partition_key)
        return response
    except Exception as exc_err:
        print ('Exception Error: kinesisPut: could not put record into stream; error:', exc_err)
