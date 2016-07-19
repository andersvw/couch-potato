#!/bin/bash

# This script is used to "deploy" the couch potato application to the local raspberry pi

RPI_USER=pi
RPI_IP=10.0.0.91

# Copy over LIRC configuration
scp lirc/lircd.conf $RPI_USER@$RPI_IP:/etc/lirc/lircd.conf
ssh $RPI_USER@$RPI_IP "sudo /etc/init.d/lirc start"

# Copy over webapp
scp -r webapp $RPI_USER@$RPI_IP:/home/pi
ssh $RPI_USER@$RPI_IP "python /home/pi/webapp/app.py" 

# TODO upload Lambda function to AWS
# TODO upload Alexa files

