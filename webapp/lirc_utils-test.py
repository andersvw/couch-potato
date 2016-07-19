from lirc_utils import LircConfig

def main():
    lirc_config = LircConfig(file_path="/etc/lirc/lircd.conf")
    remotes = lirc_config.remotes
    vizio_remote = remotes["vizio"]
    print vizio_remote.get_keys()
    print vizio_remote.send_once("KEY_MUTE")

    comcast_remote = remotes["comcast"]
    print comcast_remote.get_keys()

if __name__ == "__main__":
    main()

