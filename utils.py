import yaml, time
from types import SimpleNamespace as SN


def get_config():
    config_dir = '{0}'

    with open(config_dir.format('locale.yaml'), "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            assert False, "default.yaml error: {}".format(exc)

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