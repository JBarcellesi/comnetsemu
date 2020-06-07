#SERVER FOR AUTONOMOUS DRIVE

#Server is listening on a specific port
#It can send back date, time or both basing of the host request

#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import datetime

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ("", 65000)
print("starting up on {} port {}".format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print("waiting for a connection")
    connection, client_address = sock.accept()
    try:
        print("connection from", client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(16)
            #test = 'test'
            #test = str(datetime.datetime(2,2,2,2,2,2))
            test = str(datetime.datetime.now())
            print("received {!r}".format(data))
            if data:
                print("sending date to the client")
                connection.sendall(data)
                #connection.send(b'ciao')
                connection.sendall(str.encode(test))
            #elif data == "send hour":
            #    print("sending date to the client)
            #    connection.sendall(datetime.time)
            #elif data == "send date and hour":
            #    print("sending date and hour to the client")
            #    connection.sendall(datetime.datetime.now)
            else:
                print("no data from", client_address)
                break

    finally:
        # Clean up the connection
        connection.close()
