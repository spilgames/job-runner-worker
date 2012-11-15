Welcome to Job-Runner Worker's documentation!
=============================================

Installation
------------

Make sure all the required packages are installed:

* ``python-devel``
* ``python-virtualenv``
* ``gcc``
* ``gcc-c++``
* ``libevent-devel``

This package can be installed by executing
``pip install job-runner-worker``.


Configuration
-------------

A configuration-file is required containing the API url, api_key,
secret, etc... Example::

    [job_runner_worker]
    api_base_url=https://engportal-stg.priv.spillgroup.org/
    api_key=worker1
    secret=verysecret
    run_resource_uri=/api/v1/run/
    concurrent_jobs=4
    log_level=info
    script_temp_path=/tmp
    ws_server_hostname=websocket.server
    ws_server_port=5555
    broadcaster_server_hostname=broadcaster.server
    broadcaster_server_port=5556


``api_base_url``
    The base URL which will be used to access the API.

``api_key``
    Public-key to access the API.

``secret``
    Private-key to access the API.

``run_resource_uri``
    The URI to the run resources.

``concurrent_jobs``
    The number of jobs to run concurrently.

``log_level``
    The log level. Valid options are:

    * ``debug``
    * ``info``
    * ``warning``
    * ``error``

``ws_server_hostname``
    The hostname of the WebSocket Server.

``ws_server_port``
    The port of the WebSocket Server.

``script_temp_path``
    The path where the scripts that are being executed through the Job-Runner
    are temporarily stored. Note that this should be a location where
    executable scripts are allowed!

``broadcaster_server_hostname``
    The hostname of the queue broadcaster server.

``broadcaster_server_port``
    The port of the queue broadcaster server.


Command-line usage
------------------

For starting the worker, you can use the ``job_runner_worker`` command::

    usage: job_runner_worker [-h] [--config-path CONFIG_PATH]

    Job Runner worker

    optional arguments:
      -h, --help            show this help message and exit
      --config-path CONFIG_PATH
                            absolute path to config file (default: SETTINGS_PATH
                            env variable)
