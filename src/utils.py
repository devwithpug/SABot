import yaml, time
from types import SimpleNamespace as SN
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_config():
    with open('../config/config.yml', "r") as f:
        config = yaml.safe_load(f)

    return SN(**config).credentials

config = get_config()

print(config)

def get_locale_config():
    with open('../config/locale.yml', "r") as f:
        config = yaml.safe_load(f)

    return SN(**config)

def log(msg, guild=None):
    print_log("INFO", msg, guild)


def logErr(msg, guild=None):
    print_log("ERROR", msg, guild)


def logDebug(msg, guild=None):
    print_log("DEBUG", msg, guild)


def print_log(lvl, msg, guild=None):
    if guild is None:
        print("[{}][{}] {}".format(
            lvl,
            time.strftime("%c", time.localtime(time.time())),
            msg
        ))

    else:
        print("[{}][{}] ({}/{}) {}".format(
            lvl,
            time.strftime("%c", time.localtime(time.time())),
            guild.id,
            guild.name,
            msg
        ))