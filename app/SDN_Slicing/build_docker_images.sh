#!/bin/bash

echo "Build docker image for the echo server."
docker build -t servernew --file ./Dockerfile .

echo "Download and build mqtt-client"
docker pull aksakalli/mqtt-client

echo "Download mosquito"
docker pull eclipse-mosquitto
