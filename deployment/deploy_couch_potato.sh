#!/bin/bash

set -e

RPI_USER=pi
RPI_IP=10.0.0.91

WEBAPP_DIR=webapp
WEBAPP_DEST=/home/${RPI_USER}

LAMBDA_FUNCTION_CODE_DIR=lambda/js
LAMBDA_FUNCTION_NAME="hitLircApi"
LAMBDA_FUNCTION_ZIP="${LAMBDA_FUNCTION_NAME}.zip"
LAMBDA_FUNCTION_S3_BUCKET="couch-potato-lambda-js"

function usage {
    echo "Usage: bash deploy_couch_potato.sh [-h] [-i] [-l] [-w]"
    echo "  -h (help) print this usage message"
    echo "  -i (LIRC) deploy LIRC config to RPi"
    echo "  -l (Lambda) deploy Lambda function to AWS"
    echo "  -w (Webapp) deploy Webapp to RPi"
    exit
}

function print-separator {
    python -c "print('-' * 78)"
}

function deploy-lirc-config {
    printf "Deploying LIRC config to RPi (%s)\n\n" ${RPI_IP}
    scp lirc/lircd.conf ${RPI_USER}@${RPI_IP}:/etc/lirc/lircd.conf
    ssh ${RPI_USER}@${RPI_IP} "sudo /etc/init.d/lirc start"
    print-separator
}

# Deploy Lambda function: zip, upload to s3, update function code
function deploy-lambda-function {
    cd ${LAMBDA_FUNCTION_CODE_DIR}
    printf "Deploying Lambda function to %s\n\n" ${LAMBDA_FUNCTION_S3_BUCKET}
    printf "Zipping up Lambda function\n"
    rm -f ${LAMBDA_FUNCTION_ZIP}
    zip -r ${LAMBDA_FUNCTION_ZIP} * >/dev/null

    printf "\nUploading zip to S3\n"
    aws s3 mv ${LAMBDA_FUNCTION_ZIP} s3://${LAMBDA_FUNCTION_S3_BUCKET}/${LAMBDA_FUNCTION_ZIP}
    printf "     Modify Time     |  Size  |  Key\n"
    aws s3 ls s3://${LAMBDA_FUNCTION_S3_BUCKET} --human-readable --summarize

    printf "\nUpdating Lambda function code\n"
    aws lambda update-function-code \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --s3-bucket ${LAMBDA_FUNCTION_S3_BUCKET} \
    --s3-key ${LAMBDA_FUNCTION_ZIP}
    cd - >/dev/null
    print-separator
}

function deploy-webapp {
    printf "Deploying Webapp to RPi (%s)\n\n" ${RPI_IP}
    printf "rsync-ing %s directory\n" ${WEBAPP_DIR}
    rsync -rav -e ssh --exclude '*.pyc' --include '*' ${WEBAPP_DIR} ${RPI_USER}@${RPI_IP}:${WEBAPP_DEST}

    printf "\nKilling previous running version of couch-potato webapp\n"
    ssh ${RPI_USER}@${RPI_IP} "pkill -f app.py"

    printf "\nStarting couch-potato webapp\n"
    ssh ${RPI_USER}@${RPI_IP} "cd ${WEBAPP_DEST}/${WEBAPP_DIR}; nohup python app.py > /dev/null 2> /dev/null < /dev/null &"
    print-separator
}

# TODO upload Alexa files

# Parse arguments
while getopts "hilw" opt;
do
    case "${opt}" in
        h) usage;;
        i) LIRC="True";;
        l) LAMBDA="True";;
        w) WEBAPP="True";;
        \?) usage;;
        *) usage;;
    esac
done

# Main
printf "Deploying Couch Potato\n"
print-separator

if [ ! -z "${LIRC}" ] ; then
    deploy-lirc-config
fi
if [ ! -z "${LAMBDA}" ] ; then
    deploy-lambda-function
fi
if [ ! -z "${WEBAPP}" ] ; then
    deploy-webapp
fi

# If none of the specific components to deploy were specified, deploy them all
if [ -z "${LAMBDA}" ] && [ -z "${LIRC}" ] && [ -z "${WEBAPP}" ] ; then
    echo "No component specified, deploying everything."
    print-separator
    deploy-lirc-config
    deploy-lambda-function
    deploy-webapp
fi
