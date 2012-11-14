import ConfigParser
import logging
import os


def get_config_parser():
    """
    Return ``ConfigParser`` instance and load config file.

    This will load the settings as specified in the ``SETTINGS_PATH``
    environment variable.

    :return:
        Instance of :py:class:`ConfigParser.ConfigParser`.

    """
    config = ConfigParser.ConfigParser({
        'log_level': 'info',
    })
    config.read(os.environ['SETTINGS_PATH'])
    return config


def setup_log_handler(log_level):
    """
    Setup log handling.

    :param log_level:
        The log level (uppercased ``str``).

    """
    no_info = [
        'requests.packages.urllib3.connectionpool',
    ]

    for module in no_info:
        logging.getLogger(module).setLevel(logging.ERROR)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(levelname)s - %(asctime)s - %(name)s: %(message)s'
    )


config = get_config_parser()
