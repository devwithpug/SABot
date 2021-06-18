import yaml
from types import SimpleNamespace as SN


def get_config():
    config_dir = '{0}'

    with open(config_dir.format('locale.yaml'), "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            assert False, "default.yaml error: {}".format(exc)

    return SN(**config)