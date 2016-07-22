#!/bin/bash

# This script is used to "deploy" the couch potato application to the local raspberry pi

RPI_USER=pi
RPI_IP=10.0.0.91

WEBAPP_DIR=webapp
WEBAPP_DEST=/home/$RPI_USER

# Copy over LIRC configuration
scp lirc/lircd.conf $RPI_USER@$RPI_IP:/etc/lirc/lircd.conf
ssh $RPI_USER@$RPI_IP "sudo /etc/init.d/lirc start"

# Copy over webapp
printf "rsync-ing webapp directory to RPi (%s)\n" $RPI_IP
rsync -rav -e ssh --exclude '*.pyc' --include '*' $WEBAPP_DIR $RPI_USER@$RPI_IP:$WEBAPP_DEST

printf "Killing previous running version of couch-potato webapp\n"
ssh $RPI_USER@$RPI_IP "pkill -f webapp/app.py"

printf "Starting couch-potato webapp\n"
ssh $RPI_USER@$RPI_IP "cd ${WEBAPP_DEST}/${WEBAPP_DIR}; nohup python app.py > /dev/null 2> /dev/null < /dev/null &"

# TODO upload Lambda function to AWS
# TODO upload Alexa files
