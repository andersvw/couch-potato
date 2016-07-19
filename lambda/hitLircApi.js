'use strict';
var http = require('http');

const defaultNum = 1; // Default number of presses
const defaultRemote = "comcast";
const usage = "The Couch Potato skill can be used to control your TV and cable \
               box. Example usage includes listing all available remotes, all \
               keys for those remotes, pressing one of those keys, or changing \
               the channel.";
const turnIntentUsage = "The Turn intent is used to perform certrain options \
                         on a given target. Supported options are: on, off, up,\
                         and down. Supported targets are: TV, and options.";

var baseOptions = {
    host: '50.176.83.131',
    port: '5000',
    path: '/',
    method: 'GET'
};

var responseForAlexa = {
    "response": {
        "outputSpeech": {
            "type": "PlainText",
            "text": ""
        }
    }
};

function sendHttpRequest(options, context, callback) {
    console.log("Sending " + options.method + " request to http://" + options.host + ":" + options.port + options.path);

    var req = http.request(options, function(res) {
        var body = '';
        console.log('Status:', res.statusCode);
        console.log('Headers:', JSON.stringify(res.headers));
        res.setEncoding('utf8');
        res.on('data', function(chunk) {
            body += chunk;
        });
        res.on('end', function() {
            console.log('Successfully processed HTTP response');
            // If we know it's JSON, parse it
            if (res.headers['content-type'] === 'application/json') {
                body = JSON.parse(body);
            }
            callback(body);
        });
    });
    req.on('error', function() {
        context.fail;
    });
    req.end();
}

exports.handler = (event, context, callback) => {
    var options = baseOptions;

    switch (event.request.type) {
        case 'LaunchRequest':
            responseForAlexa.response.outputSpeech.text = usage;
            context.succeed(responseForAlexa);
            break;
        case 'IntentRequest':
            switch (event.request.intent.name) {
                case 'GetRemotes':
                    options.path = '/remotes/';
                    sendHttpRequest(options, context, function(api_response) {
                        responseForAlexa.response.outputSpeech.text = api_response.remotes.join(", ");
                        context.succeed(responseForAlexa);
                    });
                    break;
                case 'GetKeys':
                    // Handle inputs
                    const gk_remote = event.request.intent.slots.Remote.value.toLowerCase();
                    options.path = '/remotes/' + gk_remote + '/keys/';
                    
                    // Send request
                    sendHttpRequest(options, context, function(api_response) {
                        if (api_response.message) {
                            responseForAlexa.response.outputSpeech.text = api_response.message;
                        } else {
                            responseForAlexa.response.outputSpeech.text = api_response.keys.join(", ").replace(/KEY_/gi, '').toLowerCase();
                        }
                        context.succeed(responseForAlexa);
                    });
                    break;
                case 'PressKey':
                    // Handle inputs
                    const pk_remote_slot = event.request.intent.slots.Remote;
                    const pk_remote = pk_remote_slot.hasOwnProperty('value') ? pk_remote_slot.value.toLowerCase() : defaultRemote;
                    const pk_key = event.request.intent.slots.Key.value;
                    const pk_mapped_key = "KEY_" + pk_key.replace(/\s/g, '').toUpperCase();
                    const pk_num_presses_slot = event.request.intent.slots.NumPresses;
                    const pk_num_presses = pk_num_presses_slot.hasOwnProperty('value') ? pk_num_presses_slot.value : defaultNum;
                    options.path = '/remotes/' + pk_remote + '/keys/' + pk_mapped_key + "/" + pk_num_presses;
                    
                    // Send request
                    sendHttpRequest(options, context, function(api_response) {
                        if (api_response.message) {
                            responseForAlexa.response.outputSpeech.text = api_response.message;
                        } else if (api_response.irsend_rv === 0) {
                            responseForAlexa.response.outputSpeech.text = "Pressing the " + pk_key + " key " 
                                                                        + pk_num_presses + " times succeeded.";
                        } else {
                            responseForAlexa.response.outputSpeech.text = "Pressing the " + pk_key + " key " 
                                                                        + pk_num_presses + " times failed.";
                        }
                        context.succeed(responseForAlexa);
                    });
                    break;
                case 'ChangeChannel':
                    // Handle inputs
                    const cc_remote_slot = event.request.intent.slots.Remote;
                    const cc_remote = cc_remote_slot.hasOwnProperty('value') ? cc_remote_slot.value.toLowerCase() : defaultRemote;
                    const channel = event.request.intent.slots.Channel.value;
                    
                    // Decision tree
                    if (isNaN(channel)) {
                        // Look up channel name -> number mapping
                        // TODO: Create DDB table and implement look up
                    } else {
                        // Channel == channel number
                    }
                    options.path = '/remotes/' + cc_remote + '/change_channel/' + channel;
                    
                    // Send request
                    sendHttpRequest(options, context, function(api_response) {
                        if (api_response.message) {
                            responseForAlexa.response.outputSpeech.text = api_response.message;
                        } else if (api_response.irsend_rv === 0) {
                            responseForAlexa.response.outputSpeech.text = "Changing the channel to " + channel + " succeeded.";
                        } else {
                            responseForAlexa.response.outputSpeech.text = "Changing the channel to " + channel + " failed.";
                        }
                        context.succeed(responseForAlexa);
                    });
                    break;
                case 'Turn':
                    // Handle inputs
                    const turn_remote_slot = event.request.intent.slots.Remote;
                    const turn_remote = turn_remote_slot.hasOwnProperty('value') ? turn_remote_slot.value.toLowerCase() : defaultRemote;
                    const turn_option = event.request.intent.slots.Option.value;
                    const to_upper = turn_option.toUpperCase();
                    const turn_target = event.request.intent.slots.Target.value;
                    const tt_upper = turn_target.toUpperCase();
                    const turn_num_times_slot = event.request.intent.slots.NumTimes;
                    const turn_num_times = turn_num_times_slot.hasOwnProperty('value') ? turn_num_times_slot.value : defaultNum;
                    
                    // Decision tree
                    var turn_key = "KEY_";
                    if ((tt_upper == "TV") || (tt_upper == "TELEVISION")) {
                        turn_key += "POWER";
                    } else if ((tt_upper == "VOLUME") && ((to_upper == "UP") || (to_upper == "DOWN"))) {
                        turn_key += tt_upper + to_upper;
                    } else {
                        // Unhandled input values
                        responseForAlexa.response.outputSpeech.text = "The Turn intent is not configured to handle option '" + turn_option 
                                                                    + "' with target '" + turn_target + "'. Actual usage is as follows: "
                                                                    + turnIntentUsage;
                        context.succeed(responseForAlexa);
                    }
                    options.path = '/remotes/' + turn_remote + '/keys/' + turn_key + '/' + turn_num_times;
                    
                    // Send request
                    sendHttpRequest(options, context, function(api_response) {
                        if (api_response.message) {
                            responseForAlexa.response.outputSpeech.text = api_response.message;
                        } else if (api_response.irsend_rv === 0) {
                            responseForAlexa.response.outputSpeech.text = "Turning " + turn_option + " " + turn_target 
                                                                        + " " + turn_num_times + " times succeeded.";
                        } else {
                            responseForAlexa.response.outputSpeech.text = "Turning " + turn_option + " " + turn_target 
                                                                        + " " + turn_num_times + " times failed.";
                        }
                        context.succeed(responseForAlexa);
                    });
                    break;
                case 'AMAZON.HelpIntent':
                    responseForAlexa.response.outputSpeech.text = usage;
                    context.succeed(responseForAlexa);
                    break;
                default:
                    callback(new Error(`Unrecognized intent "${event.request.intent.name}"`));
            }
            break;
        case 'SessionEndedRequest':
            responseForAlexa.response.outputSpeech.text = "Couch Potato session ended";
            context.succeed(responseForAlexa);
            break;
        default:
    }
};
