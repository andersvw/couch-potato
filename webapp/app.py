from custom_exceptions import IllegalArgumentError, InvalidAPIUsageException
from flask import Flask, render_template, jsonify, request
from lirc_utils import LircConfig
import time


lirc_config = LircConfig()
app = Flask(__name__)

""" UTILITY METHODS """
def get_remote(remote_name):
    try:
        return lirc_config.remotes[remote_name]
    except KeyError:
        raise InvalidAPIUsageException("No remote defined for name '{0}' in lirc config '{1}'".format(remote_name, lirc_config.config_file_path))

def press_key(remote, key, num_presses=1):
    try:
        return remote.send(key, num_presses=num_presses)
    except IllegalArgumentError, e:
        raise InvalidAPIUsageException(e.message)

def press_keys(remote, keys):
    try:
        return remote.send_all(keys)
    except IllegalArgumentError, e:
        raise InvalidAPIUsageException(e.message)

def parse_int_from_url(string):
    try:
        return int(string)
    except ValueError:
        raise InvalidAPIUsageException("The parameter must be an integer. '{0}' was passed.".format(string))

""" ERROR HANDLERS """
@app.errorhandler(InvalidAPIUsageException)
def handle_invalid_api_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

""" ROUTES """
@app.route('/')
def index_route():
    return render_template('index.html') 

@app.route('/remotes/', methods=['GET'])
def get_remotes_route():
    return jsonify({'remotes': lirc_config.remotes.keys()})

@app.route('/remotes/<remote_name>/', methods=['GET'])
def get_all_remote_info_route(remote_name):
    return jsonify(get_remote(remote_name).serialize())

@app.route('/remotes/<remote_name>/keys/', methods=['GET'])
def get_remote_keys_route(remote_name):
    return jsonify({'remote': remote_name, 'keys': get_remote(remote_name).keys})

@app.route('/remotes/<remote_name>/press-key')
def press_key_route(remote_name):
    remote = get_remote(remote_name)
    num_presses = request.args.get('num-presses', default=1, type=int)
    num_presses = request.args.get('num-presses') if request.args.get('num-presses') else 1

    if num_presses < 1:
        raise InvalidAPIUsageException("The channel parameter cannot be more than 4 digits. '{0}' was passed.".format(channel))

    irsend_rv = press_key(remote, key_name, num_presses=num_presses)
    return jsonify({'remote': remote_name, 'key': key_name, 'irsend_rv': irsend_rv})

@app.route('/remotes/<remote_name>/keys/<key_name>')
def press_key_route_old(remote_name, key_name):
    remote = get_remote(remote_name)
    irsend_rv = press_key(remote, key_name)
    return jsonify({'remote': remote_name, 'key': key_name, 'irsend_rv': irsend_rv})

# This can probably be folded into the above method as a query param
@app.route('/remotes/<remote_name>/keys/<key_name>/<number_of_presses>')
def press_key_multi_route(remote_name, key_name, number_of_presses):
    remote = get_remote(remote_name)
    num_presses = parse_int_from_url(number_of_presses)

    if num_presses < 1:
        raise InvalidAPIUsageException("The channel parameter cannot be more than 4 digits. '{0}' was passed.".format(channel))

    irsend_rv = press_key(remote, key_name, num_presses=num_presses)
    return jsonify({'remote': remote_name, 'key': key_name, 'irsend_rv': irsend_rv})

# This should be handled as a query parameter or maybe as a POST request
#
# Store mapping of channel names to numbers either here in python or a text file
# or store this in DDB and have the lambda function access it based on the input type
@app.route('/remotes/<remote_name>/change_channel/<channel>')
def change_channel_route(remote_name, channel):
    remote = get_remote(remote_name)
    parse_int_from_url(channel)
    
    if len(channel) > 4:
        raise InvalidAPIUsageException("The channel parameter cannot be more than 4 digits. '{0}' was passed.".format(channel))

    keys = []
    for number in channel:
        keys.append("KEY_" + number)
    keys.append("KEY_OK")

    irsend_rv = press_keys(remote, keys)

    return jsonify({'remote': remote_name, 'channel': channel, "irsend_rv": irsend_rv})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0')
