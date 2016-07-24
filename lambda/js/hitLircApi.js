'use strict';
var APP_ID = "amzn1.echo-sdk-ams.app.9dc76818-c3a0-4293-b33e-c74aedec6c34";

var http = require('http');
var Alexa = require('alexa-sdk');

const defaultNumPresses = 1; // Default number of presses
const defaultRemote = "comcast";
const defaultKey = "OK";

const usage = "The Couch Potato skill can be used to control your TV and cable box. Example usage includes listing all \
               available remotes, all keys for those remotes, pressing one of those keys, or changing the channel.";
const turnIntentUsage = "The Turn intent is used to perform certain options on a given target. Supported options are: \
                         on, off, up, and down. Supported targets are: TV, and options.";

var baseOptions = {
    host: '50.176.83.131',
    port: '5000',
    path: '/',
    method: 'GET'
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

function getRemotes() {
    var handler = this;
    var options = baseOptions;
    options.path = '/remotes/';
    sendHttpRequest(options, handler.context, function(api_response) {
        handler.emit(':tell', api_response.remotes.join(", "));
    });
}

function getKeys() {
    var handler = this;
    var options = baseOptions;

    const remote = handler.event.request.intent.slots.Remote.value.toLowerCase();
    options.path = '/remotes/' + remote + '/keys/';

    sendHttpRequest(options, handler.context, function(api_response) {
        if (api_response.message) {
            handler.emit(':tell', api_response.message);
        } else {
            handler.emit(':tell', api_response.keys.join(", ").replace(/KEY_/gi, '').toLowerCase());
        }
    });
}

function pressKey() {
    var handler = this;
    var options = baseOptions;

    const remote = handler.event.request.intent.slots.Remote.value || defaultRemote;
    const key = handler.event.request.intent.slots.Key.value || defaultKey;
    const mapped_key = "KEY_" + key.replace(/\s/g, '').toUpperCase();
    const num_presses = handler.event.request.intent.slots.NumPresses.value || defaultNumPresses;
    options.path = '/remotes/' + remote + '/press-key/' + mapped_key + '?num-presses=' + num_presses;

    sendHttpRequest(options, handler.context, function(api_response) {
        if (api_response.message) {
            handler.emit(':tell', api_response.message);
        } else if (api_response.irsend_rv === 0) {
            handler.emit(':tell', "Pressing the " + key + " key " + num_presses + " times succeeded.");
        } else {
            handler.emit(':tell', "Pressing the " + key + " key " + num_presses + " times failed.");
        }
    });
}

function changeChannel() {
    var handler = this;
    var options = baseOptions;

    const remote = handler.event.request.intent.slots.Remote.value || defaultRemote;
    var channel = handler.event.request.intent.slots.Channel.value;

    if (isNaN(channel)) {
        // TODO: Create DDB table and implement look up
        console.log("Channel = " + channel)
        switch (channel.toUpperCase()) {
            case "CBS":
                channel = 804;
                break;
            case "ABC":
                channel = 805;
                break;
            case "FOX":
                channel = 806;
                break;
            case "NBC":
                channel = 807;
                break;
            case "NHL NETWORK":
                channel = 822;
                break;
            case "ESPN":
                channel = 849;
                break;
            case "COMEDY CENTRAL":
                channel = 858;
                break;
            case "AMC":
                channel = 859;
                break;
            case "CARTOON NETWORK":
                channel = 860;
                break;
            case "HBO SIGNATURE":
                channel = 869;
                break;
            case "HBO":
                channel = 870;
                break;
            case "HBO2":
                channel = 871;
                break;
            default:
                // do nothing, backend will fail request due to NaN
                break;
        }
    }
    options.path = '/remotes/' + remote + '/change_channel/' + channel;

    sendHttpRequest(options, handler.context, function(api_response) {
        if (api_response.message) {
            handler.emit(':tell', api_response.message);
        } else if (api_response.irsend_rv === 0) {
            handler.emit(':tell', "Changing the channel to " + channel + " succeeded.");
        } else {
            handler.emit(':tell', "Changing the channel to " + channel + " failed.");
        }
    });
}

function turn() {
    var handler = this;
    var options = baseOptions;

    const remote = handler.event.request.intent.slots.Remote.value || defaultRemote;
    const option = handler.event.request.intent.slots.Option.value.toUpperCase();
    const target = handler.event.request.intent.slots.Target.value.toUpperCase();
    const num_times = handler.event.request.intent.slots.NumTimes.value || defaultNumPresses;

    var key = "KEY_";
    if ((target == "TV") || (target == "TELEVISION")) {
        key += "POWER";
    } else if ((target == "VOLUME") && ((option == "UP") || (option == "DOWN"))) {
        key += target + option;
    } else {
        handler.emit(':tell', "The Turn intent is not configured to handle option '" + option + "' with target '"
                              + target + "'. Actual usage is as follows: " + turnIntentUsage);
        return;
    }
    options.path = '/remotes/' + remote + '/press-key/' + key + '?num-presses=' + num_times;

    sendHttpRequest(options, handler.context, function(api_response) {
        if (api_response.message) {
            handler.emit(':tell', api_response.message);
        } else if (api_response.irsend_rv === 0) {
            handler.emit(':tell', "Turning " + option + " " + target + " " + num_times + " times succeeded.");
        } else {
            handler.emit(':tell', "Turning " + option + " " + target + " " + num_times + " times failed.");
        }
    });
}

var handlers = {
    'LaunchRequest': function() { this.emit(':tell', "Hello from Couch Potato!"); },
    'GetRemotesIntent': getRemotes,
    'GetKeysIntent': getKeys,
    'PressKeyIntent': pressKey,
    'ChangeChannelIntent': changeChannel,
    'TurnIntent': turn,
    'AMAZON.HelpIntent': function() { this.emit(':tell', usage); },
    'SessionEndedRequest': function() { this.emit(':tell', "Good bye from Couch Potato!"); }
};

exports.handler = function(event, context, callback) {
    var alexa = Alexa.handler(event, context);
    alexa.appId = APP_ID;
    alexa.registerHandlers(handlers);
    alexa.execute();
};
