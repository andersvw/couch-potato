from custom_exceptions import IllegalArgumentError
import re
import subprocess

DEFAULT_LIRC_CONFIG_LOCATION = "/etc/lirc/lircd.conf"

# the question mark in .*? makes the .* match as few characters as possible
REMOTE_PATTERN = re.compile('begin remote[\S\s]*?name\s*(.+)[\S\s]*?([\S\s]*?)end remote')
REMOTE_INFO_PATTERN = re.compile('')
CODES_PATTERN = re.compile('begin codes([\S\s]*?)end codes')
CODE_PATTERN = re.compile('([A-Z_]+)\s+([x0-9A-F]+)')
RAW_CODES_PATTERN = re.compile('begin raw_codes([\S\s]*?)end raw_codes')
RAW_CODE_PATTERN = re.compile('name ([A-Z_0-9]+)([0-9\s\n]*)')
NUMBERS_PATTERN = re.compile('[0-9]+')

class Remote():
    name = ""
    keys = [] # list of all possible keys/buttons defined for a given remote
    codes = [] # list of all codes defined for a given remote
    raw_codes = [] # list of all raW_codes defined for a given remote

    def __init__(self, name, keys, codes, raw_codes):
        self.name = name
        self.keys = keys
        self.codes = codes
        self.raw_codes = raw_codes

    def __str__(self):
        return "\"name\": {0}, \"keys\": {1}, \"codes\": {2}, \"raw_codes\": {3}".format(self.name, self.keys, self.codes, self.raw_codes)
    
    def __repr__(self):
        return self.__str__()

    def serialize(self):
        return {
            'name': self.name,
            'keys': self.keys,
            'codes': [code.serialize() for code in self.codes],
            'raw_codes': [raw_code.serialize() for raw_code in self.raw_codes]
        }

    def get_keys(self):
        return self.keys

    def send(self, key, num_presses=1):
        if not type(num_presses) is int:
            raise IllegalArgumentError("Illegal argument passed. Number of key presses must be an integer. {0} was passed.".format(num_presses))
        elif num_presses < 1:
            raise IllegalArgumentError("Illegal argument passed. Number of key presses must be greater than 1. {0} was passed.".format(num_presses))

        if key in self.keys:
            # Because the TV has de-bounce protection and irsend sends the values too quickly, we need to send each
            # key press twice, except for the first.
            args = ['irsend', 'SEND_ONCE', self.name] + [key] + [key] * (2 * (num_presses - 1))
            return subprocess.call(args)
        else:
            raise IllegalArgumentError("Illegal argument passed. Remote '{0}' has no key '{1}'.".format(self.name, key))

    def send_all(self, keys):
        for key in keys:
            if not key in self.keys:
                raise IllegalArgumentError("Illegal argument passed. Remote '{0}' has no key '{1}'.".format(self.name, key))
        else: 
            args = ['irsend', 'SEND_ONCE', self.name] + keys
            return subprocess.call(args)

class Code():
    name = ""
    value = ""

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "\"name\": {0}, \"value\": {1}".format(self.name, self.value)
    
    def __repr__(self):
        return self.__str__()
    
    def serialize(self):
        return {
            'name': self.name,
            'value': self.value
        }

class RawCode():
    name = ""
    values = []

    def __init__(self, name, values):
        self.name = name
        self.values = values

    def __str__(self):
        return "\"name\": {0}, \"values\": {1}".format(self.name, self.values)
    
    def __repr__(self):
        return self.__str__()

    def serialize(self):
        return {
            'name': self.name,
            'values': self.values
        }

class LircConfig():
    remotes = {} # Entries of the form "remote_name" : Remote

    def __init__(self, config_file_path=DEFAULT_LIRC_CONFIG_LOCATION):
        self.config_file_path = config_file_path
        self.parse_config_file(config_file_path)

    def parse_config_file(self, config_file_path):
        print "Parsing config file '{0}'...".format(config_file_path)
        with open(config_file_path, 'r') as f:
            file_text = f.read()

            remote_matches = REMOTE_PATTERN.finditer(file_text)
            for remote_match in remote_matches:
                remote_name = remote_match.group(1)

                keys = []
                codes = []
                raw_codes = []

                codes_search = CODES_PATTERN.search(remote_match.group(2))
                if codes_search:
                    code_matches = CODE_PATTERN.finditer(codes_search.group(1))    
                    for code_match in code_matches:
                        code_name = code_match.group(1)
                        code_value = code_match.group(2)

                        keys.append(code_name)
                        codes.append(Code(code_name, code_value))
                        
                        #print "Found code: ({0}, {1})".format(code_name, code_value)
                    #print "Found {0} codes in {1}".format(len(codes), remote_name)

                raw_codes_search = RAW_CODES_PATTERN.search(remote_match.group(2))
                if raw_codes_search:
                    raw_code_matches = RAW_CODE_PATTERN.finditer(raw_codes_search.group(1))
                    for raw_code_match in raw_code_matches:
                        raw_code_name = raw_code_match.group(1)
                        raw_code_values_string = raw_code_match.group(2)
                        raw_code_values = re.split("(?:\s+|\n)", raw_code_values_string)
                        
                        keys.append(raw_code_name)
                        raw_codes.append(RawCode(raw_code_name, raw_code_values))

                        #print "Found raw_code: ({0}, {1})".format(raw_code_name, raw_code_values)
                    #print "Found {0} raw_codes in {1}".format(len(raw_codes), remote_name)
                
                self.remotes[remote_name] = Remote(remote_name, keys, codes, raw_codes)
            print "Found {0} defined remotes in '{1}': {2}".format(len(self.remotes), config_file_path, self.remotes.keys())


