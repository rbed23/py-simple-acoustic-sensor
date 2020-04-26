'''Contains useful modules for the Acoustic Sensors Prototype Device'''
# !/usr/bin/env python
from __future__ import print_function
import json
import sys
import ssl

from AWSIoTPythonSDK.core.protocol.paho import client as mqtt


def setup_iot_device(config):
    '''
    Setup and config IoT device configuration for AWS
    <type config: str
    <desc config: directory path to config file

    <<type device>> dict
    <<desc device>> device configuration values
    '''
    try:
        with open(config, 'rb') as j:
            cfg = json.load(j)
    except Exception as exc_err:
        print(f"Error: Unable to load configuration file\n{exc_err}")
        sys.exit()
    try:
        device = {
            "endpoint_url": cfg['aws_vars']['awsendpoint'],
            "endpoint_port": cfg['aws_vars']['awsendpoint_port'],
            "client_id": cfg['aws_vars']['clientId'],
            "ca_file": cfg['aws_vars']['caPath'],
            "key_file": cfg['aws_vars']['keyPath'],
            "cert_file": cfg['aws_vars']['certPath'],
            "in_channels": cfg['aws_vars']['subscribe_topics'],
            "out_channels": cfg['aws_vars']['publish_topics']
        }
    except Exception as exc_err:
        print(f"Error: Unable to configure device\n{exc_err}")
        sys.exit()
    else:
        return device


def get_iot_client(device):
    '''
    Setup and config AWS IoT client
    <type device> dict
    <desc device> device configuration values

    <<type client>> AWS IoT Client Object
    <<desc client>> none
    '''
    try:
        client = mqtt.Client(device['clientId'])
        client.bad_connection_flag = False
        client.bad_auth_flag = False
        client.connected_flag = False
        client.disconnected_flag = False

        client.on_connect = onConnect
        client.on_disconnect = onDisconnect
        client.on_message = onMessage
        '''
        client.on_publish = onPublish
        client.on_subscribe = onSubscribe
        client.on_unsubscribe = onUnsubscribe
        client.on_log = onLog
        '''
    except TypeError as typ_err:
        print(f"Type Error: {typ_err}")
    except Exception as exc_err:
        print(f"Error: binding callbacks failure\n{exc_err}")
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
            print(f"Error: setting TLS credentials failure\n{exc_err}")
            sys.exit()
        else:
            return client


def onConnect(client, userdata, flags, rc):
    '''
    Successful connection callback handler

    <type client> AWS IoT Client
    <desc client> instance connected to broker

    <type userdata> any
    <desc userdata> see AWSIoTPythonSDK.core.protocol.paho.client L340

    <type flags> dict
    <desc flags> contains response flags from the broker
        see AWSIoTPythonSDK.core.protocol.paho.client L347

    <type rc> int
    <desc rc> response code from connection attempt
        see AWSIoTPythonSDK.core.protocol.paho.client L353
    '''
    if rc == 0:
        client.connected_flag = True
        client.disconnected_flag = False
        print(f"Client ID: {client._client_id} connected")
    else:
        client.bad_connection_flag = True
        print(f"MQTT RC Error: {mqtt.error_string(rc)}")
        print(f"Lookup RC designation << {rc} >> in "
              f"AWSIoTPythonSDK.core.protocol.paho.client "
              f"documentation (L353) for more information")


def onDisconnect(client, userdata, rc):
    '''
    Disconnection callback handler, purposeful or otherwise

    <type client> mqtt paho Client instance
    <desc client> Client instance that disconnected from broker

    <type userdata> any
    <desc userdata> see AWSIoTPythonSDK.core.protocol.paho.client L340

    <type rc> int
    <desc rc> value of rc determines success or not
        see AWSIoTPythonSDK.core.protocol.paho.client L353
    '''
    client.connected_flag = False
    client.disconnected_flag = True
    print(f"MQTT Disconnection; return code = {rc}")


def onMessage(client, userdata, message):
    print(f"Message received from << {message.topic} >>")
    print(f"{json.dumps(message.payload, indent=2)}")


def subscriber(client, device):
    '''
    Executes subscription to a list of desired topics

    <type client> AWS IoT Client
    <desc client> instance subscribing to broker

    <type device> dict
    <desc device> device configuration values
    '''
    # break channels into tuples (AWS Client.subscribe method reqr)
    subscribing = [(update_channel(eachchannel, device['client_id']), 1)
                   for eachchannel in device['in_channels']]

    # break tuples into chunks (AWS Client.subscribe method limit)
    chunks = [subscribing[x:x+8] for x in range(0, len(subscribing), 8)]
    for chunk in chunks:
        sub_resp = client.subscribe(chunk)
        subscribe_statement(client, chunk, sub_resp)


def subscribe_statement(client, sub_list, resp):
    '''
    Outputs Subscribe Statement to Console

    <type client> AWS IoT Client
    <desc client> n/a

    <type sub_list> list
    <desc sub_list> list of channels that meet the AWS topic specifications
        [https://docs.aws.amazon.com/iot/latest/
        developerguide//thing-shadow-mqtt.html#get-pub-sub-topic]
        [https://docs.aws.amazon.com/general/latest/
        gr/aws_service_limits.html#limits_iot]

    <type resp> tuple
    <desc resp> in format (result, mid), where result is MQTT_ERR_SUCCESS to
        indicate success or MQTT_ERR_NO_CONN if the client is not currently
        connected.  mid is the message ID for the subscribe request.
    '''
    print(f"{client._client_id} subscribed to the following channels:")
    for sub in sub_list:
        print(f"   {sub[0]} with QoS: {sub[1]}")


def update_channel(channel, id):
    if '<clientId>' in channel:
        return channel.replace('<clientId>', id)
    else:
        return channel
