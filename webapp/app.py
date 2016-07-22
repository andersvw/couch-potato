import argparse
import logging

from flask import Flask, render_template, jsonify, request

from lib.custom_exceptions import IllegalArgumentError, InvalidAPIUsageException
from lib.lirc_utils import LircConfig, DEFAULT_LIRC_CONFIG_LOCATION

logging.basicConfig(filename="app.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s")

lirc_config = LircConfig(DEFAULT_LIRC_CONFIG_LOCATION)
app = Flask(__name__)

""" UTILITY METHODS """
def get_remote(remote_name):
    try:
        return lirc_config.remotes[remote_name]
    except KeyError:
        raise InvalidAPIUsageException("No remote defined for name '{0}' in lirc config.".format(remote_name))


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
    """
    Error handler for InvalidAPIUsageExceptions. This handler adds the exception's HTTP status code to the response.
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


""" ROUTES """
@app.route('/')
def index_route():
    logging.info("Rendering index page.")
    return render_template('index.html')


@app.route('/remotes/', methods=['GET'])
def get_remotes_route():
    logging.info("Getting all remotes.")
    return jsonify({'remotes': lirc_config.remotes.keys()})


@app.route('/remotes/<remote_name>/', methods=['GET'])
def get_all_remote_info_route(remote_name):
    logging.info("Getting all remote info for remote %s.", remote_name)
    return jsonify(get_remote(remote_name).serialize())


@app.route('/remotes/<remote_name>/keys/', methods=['GET'])
def get_remote_keys_route(remote_name):
    logging.info("Getting keys for remote %s.", remote_name)
    return jsonify({'remote': remote_name, 'keys': get_remote(remote_name).keys})


@app.route('/remotes/<remote_name>/press-key/<key_name>')
def press_key_route(remote_name, key_name):
    """
    Press a given key on a given remote. If the query parameter num-presses is set, press the key that number of times.
    Otherwise, only press the key once.

    NOTE: Logically, this might be better implemented as a POST request.
    """
    remote = get_remote(remote_name)
    num_presses = request.args.get('num-presses', default=1, type=int)

    if num_presses < 1:
        raise InvalidAPIUsageException(
            "The number of presses parameter must be >= 1. '{0}' was passed.".format(num_presses))

    irsend_rv = press_key(remote, key_name, num_presses=num_presses)
    logging.info("Pressing key %s %d times %s.", key_name, num_presses, "SUCCEEDED" if not irsend_rv else "FAILED")
    return jsonify({'remote': remote_name, 'key': key_name, 'irsend_rv': irsend_rv})


@app.route('/remotes/<remote_name>/keys/<key_name>')
def press_key_route_old(remote_name, key_name):
    """
    DEPRECATED - use press_key_route() above

    Press a given key on a given remote a single time.
    """
    remote = get_remote(remote_name)
    irsend_rv = press_key(remote, key_name)
    logging.info("Pressing key %s %s.", key_name, "SUCCEEDED" if not irsend_rv else "FAILED")
    return jsonify({'remote': remote_name, 'key': key_name, 'irsend_rv': irsend_rv})


@app.route('/remotes/<remote_name>/keys/<key_name>/<number_of_presses>')
def press_key_multi_route(remote_name, key_name, number_of_presses):
    """
    DEPRECATED - use press_key_route() above with the num-presses query param in the URL

    Press a given key on a given remote a given number of times.
    """
    remote = get_remote(remote_name)
    num_presses = parse_int_from_url(number_of_presses)

    if num_presses < 1:
        raise InvalidAPIUsageException(
            "The number of presses parameter must be >= 1. '{0}' was passed.".format(num_presses))

    irsend_rv = press_key(remote, key_name, num_presses=num_presses)
    logging.info("Pressing key %s %d times %s.", key_name, num_presses, "SUCCEEDED" if not irsend_rv else "FAILED")
    return jsonify({'remote': remote_name, 'key': key_name, 'irsend_rv': irsend_rv})


@app.route('/remotes/<remote_name>/change_channel/<channel>')
def change_channel_route(remote_name, channel):
    """
    Change to the specified channel with the given remote.

    NOTE: Logically, this might be better implemented as a POST request.
    TODO [2016-07-21]: Store mappings of channel names to numbers either in here in python, a text file, or in DDB and
     have the lambda function access it based on the input type
    """
    remote = get_remote(remote_name)
    parse_int_from_url(channel)

    if len(channel) > 4:
        raise InvalidAPIUsageException(
            "The channel parameter cannot be more than 4 digits. '{0}' was passed.".format(channel))

    keys = []
    for number in channel:
        keys.append("KEY_" + number)
    keys.append("KEY_OK")

    irsend_rv = press_keys(remote, keys)
    logging.info("Changing channel to %s %s.", channel, "SUCCEEDED" if not irsend_rv else "FAILED")
    return jsonify({'remote': remote_name, 'channel': channel, "irsend_rv": irsend_rv})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='flag to run the Flask app in debug mode')
    args = parser.parse_args()

    logging.info("Starting app in %s mode", 'debug' if args.debug else 'normal')
    app.run(debug=args.debug, use_reloader=False, host='0.0.0.0')


if __name__ == '__main__':
    main()
