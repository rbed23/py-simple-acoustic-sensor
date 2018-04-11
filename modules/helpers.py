'''Contains useful modules for the Acoustic Sensors Prototype Device'''
#!/usr/bin/env python
from __future__ import print_function
import json, random, string, base64
import time, datetime

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