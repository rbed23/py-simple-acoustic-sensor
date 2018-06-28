'''Contains useful modules for the Acoustic Sensors Prototype Device'''
#!/usr/bin/env python
from __future__ import print_function
import json, sys, ssl
from AWSIoTPythonSDK.core.protocol.paho import client as mqtt

### setup IoT client
def setup_iot_device(config):
    '''
    Setup and config IoT device configuration for AWS
    :type config: str
    :param config: directory path to config file

    :return:
    :type device: dict
    :param device: none
    '''
    try:
        with open(config, 'rb') as j:
            cfg = json.load(j)
    except Exception as exc_err:
        print ('Exception Error: Unable to open and load configuration file from location;', str(exc_err))
        sys.exit()
    try:
        device = {
            "endpoint_url" : cfg['aws_vars']['awsendpoint'],
            "endpoint_port" : cfg['aws_vars']['awsendpoint_port'],
            "clientId" : cfg['aws_vars']['clientId'],
            "caFile" : cfg['aws_vars']['caPath'],
            "keyFile" : cfg['aws_vars']['keyPath'],
            "certFile" : cfg['aws_vars']['certPath'],
            "in_channels" : cfg['aws_vars']['subscribe_topics'],
	    "out_channel" : cfg['aws_vars']['publish_topic']
        }
    except Exception as exc_err:
        print ('Exception Error: Unable to setup the device based on config file;', str(exc_err))
        sys.exit()
    else:
        return device

def get_iot_client(device):
    '''
    Setup and config AWS IoT client
    :type device: dict object
    :param device: with relevant k-v pairs needed to setup client

    :return:
    :type client: AWS IoT client
    :param client: none
    '''
    try:
        client = mqtt.Client(device['clientId'])
        #set flags
        client.bad_connection_flag = False
        client.bad_auth_flag = False
        client.connected_flag = False
        client.disconnected_flag = False

        client.on_connect = onConnect
        client.on_disconnect = onDisconnect
        client.on_message = onMessage
        #client.on_publish = onPublish
        #client.on_subscribe = onSubscribe
        #client.on_unsubscribe = onUnsubscribe
        #client.on_log = onLog
    except TypeError as typ_err:
        print ('Type Error:', str(typ_err))
        print ('   Look at IoT device configuration location and settings')
    except: 
        print ('Exception Error: error binding callbacks to MQTT Client')
    else:
        try:
            client.tls_set(
                ca_certs=device['caFile'],
                certfile=device['certFile'],
                keyfile=device['keyFile'],
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_SSLv23,
                ciphers=None)
        except Exception as exc_err:
            print ('Exception Error: error setting tls credentials;', str(exc_err))
            sys.exit()
        else:
            return client

# Initialize the MQTT on_connect callback function
def onConnect(client,userdata,flags,rc):
    '''
    Successful connection callback handler

    :type client: mqtt paho Client instance
    :param client: Client instance that connected to broker

    :type userdata: any
    :param userdata: see AWSIoTPythonSDK.core.protocol.paho.client L340

    :type flags: dict
    :param flags: contains response flags from the broker
        see AWSIoTPythonSDK.core.protocol.paho.client L347

    :type rc: int
    :param rc: value of rc determines success or not
        see AWSIoTPythonSDK.core.protocol.paho.client L353
    '''
    if rc == 0:
        client.connected_flag = True
        client.disconnected_flag = False
        print ("Client ID: " + client._client_id + ' connected')
    elif rc == 1:
        print ("MQTT Authorization Error - Connection Refused - Incorrect Protocol Version; return code =", rc)
        client.bad_connection_flag = True
    elif rc == 2:
        print ("MQTT Authorization Error - Connection Refused - Invalid Client Identifier; return code =", rc)
        client.bad_connection_flag = True
    else:
        print ("MQTT Connection Error: bad connection attempt; return code =", rc)
        client.bad_connection_flag = True

# Initialize the MQTT on_disconnect callback function
def onDisconnect(client,userdata,rc):
    '''
    Disconnection callback handler, purposeful or otherwise

    :type client: mqtt paho Client instance
    :param client: Client instance that disconnected from broker

    :type userdata: any
    :param userdata: see AWSIoTPythonSDK.core.protocol.paho.client L340

    :type rc: int
    :param rc: value of rc determines success or not
        see AWSIoTPythonSDK.core.protocol.paho.client L353
    '''
    client.connected_flag = False
    client.disconnected_flag = True
    print ("MQTT Disconnection; return code =", rc)

# Initialize the MQTT on_message callback function
def onMessage(client, userdata, message):
    print ("Message received from " + message.topic)
    print (json.dumps(message.payload, indent = 2))

# Subscribe to topics
def subscriber_fx(client, device):
    '''
    Executes subscription to a list of desired topics

    :type client: mqtt paho Client instance
    :param client: Client instance that wants to subscribe to broker

    :type device: dict object
    :param device: valid dict object
    '''
    subscribe_list = []
    for eachchannel in device['in_channels']:
        channel = update_channel(eachchannel, device['clientId'])
        tup = (str(channel), 1)
        subscribe_list.append(tup)

    if len(subscribe_list) <= 8:
        sub_resp = client.subscribe(subscribe_list)
        subscribe_statement(client, subscribe_list, sub_resp)
    else: # can only subscribe to max 8 topics at a time in a single call
        subscribe_chunks = [subscribe_list[x:x+8] for x in xrange(0, len(subscribe_list), 8)]
        for each_chunk in subscribe_chunks:
            sub_resp = client.subscribe(each_chunk)
            subscribe_statement(client, each_chunk, sub_resp)

def subscribe_statement(client, sub_list, resp):
    '''
    Outputs Subscribe Statement to Console

    :type client: mqtt paho Client object
    :param client: n/a

    :type sub_list: list
    :param sub_list: list of channels that meet the AWS topic specifications
        [https://docs.aws.amazon.com/iot/latest/
        developerguide//thing-shadow-mqtt.html#get-pub-sub-topic]
        [https://docs.aws.amazon.com/general/latest/
        gr/aws_service_limits.html#limits_iot]

    :type resp: tuple
    :param resp: in format (result, mid), where result is MQTT_ERR_SUCCESS to
        indicate success or MQTT_ERR_NO_CONN if the client is not currently
        connected.  mid is the message ID for the subscribe request.
    '''
    print ('Subscribe: ' + client._client_id + " subscribed to the following channels:")
    for each in sub_list:
        print ("   QoS: " + str(each[1]) + " '" + each[0] + "'")

def update_channel(channel, id):
    if '<clientId>' in channel:
	    upd_channel = channel.replace('<clientId>', id)
	    return upd_channel
    else:
	    return channel
