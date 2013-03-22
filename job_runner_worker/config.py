import ConfigParser
import logging
import os


def get_config_parser():
    """
    Return ``ConfigParser`` instance and load config file.

    This will load the settings as specified in the ``CONFIG_PATH``
    environment variable.

    :return:
        Instance of :py:class:`ConfigParser.ConfigParser`.

    """
    config = ConfigParser.ConfigParser({
        'log_level': 'info',
        'max_log_bytes': str(800 * 1024),
        'worker_resource_uri': '/api/v1/worker/',
        'run_resource_uri': '/api/v1/run/',
        'run_log_resource_uri': '/api/v1/run_log/',
        'kill_request_resource_uri': '/api/v1/kill_request/',
        'concurrent_jobs': '4',
        'ws_server_port': '5555',
        'broadcaster_server_port': '5556',
        'reconnect_after_inactivity': str(60 * 10),
        'script_temp_path': '/tmp',
    })
    config.read(os.environ['CONFIG_PATH'])
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
