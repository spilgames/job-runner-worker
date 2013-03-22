Job-Runner Worker
=================

This package contains the Job-Runner Worker, which is responsible for executing
the scheduled jobs managed by the Job-Runner.

Links
-----

* `documentation <https://job-runner.readthedocs.org/>`_
* `source <https://github.com/spilgames/job-runner-worker/>`_


Installation
------------

Requirements (depending on your distro, the naming might be a bit different):

* ``python-dev``
* ``build-essential``
* ``libevent-dev``

Then you should be able to install this package with
``pip install job-runner-worker``.

If you want to install this package in development mode, clone this repository
and then execute ``python setup.py develop``. In the latter, you might want
to install the testing requirements by executing
``pip install -r test-requirements.txt``.

See the getting started section in the Job-Runner documentation (
in the *job-runner* repo) for setting up the whole project.


Configuration
-------------

Example with required settings::

    [job_runner_worker]
    api_base_url=http://domain.of.job.runner/
    api_key=worker1
    secret=verysecret
    script_temp_path=/tmp
    ws_server_hostname=domain.of.websocket.server
    broadcaster_server_hostname=domain.of.broadcast.server


All available settings
~~~~~~~~~~~~~~~~~~~~~~

``api_base_url``
    The base URL which will be used to access the API. This should start with
    ``http://`` or ``https://``.

``api_key``
    Public-key to access the API.

``secret``
    Private-key to access the API.

``concurrent_jobs``
    The number of jobs to run concurrently. Default: ``4``.

``log_level``
    The log level. Default: ``'info'``. Valid options are:

    * ``debug``
    * ``info``
    * ``warning``
    * ``error``

``max_log_bytes``
    The maximum number of bytes of the log that is sent back to the API. This
    is to avoid ``413 Request Entity Too Large`` errors. If the log will be
    larger than this value, 20% of the allowed size will be taken from the top
    of the log, the remaining 80% will be taken from the bottom. Everything
    in between will be truncated. Default: ``819200`` (800kb).

``ws_server_hostname``
    The hostname of the WebSocket Server.

``ws_server_port``
    The port of the WebSocket Server. Default: ``5555``.

``script_temp_path``
    The path where the scripts that are being executed through the Job-Runner
    are temporarily stored. Default: ``'/tmp'``.

``broadcaster_server_hostname``
    The hostname of the queue broadcaster server.

``broadcaster_server_port``
    The port of the queue broadcaster server. Default: ``5556``.

``reconnect_after_inactivity``
    Seconds after which the subscriber is re-connecting to the publisher
    when no data has been received. Default: ``300``. This is useful when you
    are loadbalancing the publisher and it keeps the TCP connection open on the
    front-end, when the connection on the back-end has been closed. Because of
    this ZMQ doesn't detect that it is not connected anymore and jobs get
    stuck.


Command-line usage
------------------

For starting the worker, you can use the ``job_runner_worker`` command::

    usage: job_runner_worker [-h] [--config-path CONFIG_PATH]

    Job Runner worker (v2.0.0)

    optional arguments:
      -h, --help            show this help message and exit
      --config-path CONFIG_PATH
                            absolute path to config file (default: CONFIG_PATH env
                            variable)


Changes
-------

v2.0.0
~~~~~~

* Make the worker compatible with the new worker-pool structure.
  **IMPORTANT:** This version is dependent on ``job-runner>=2.0.0``!
* Change ``SETTINGS_PATH`` environment variable to ``CONFIG_PATH`` for better
  naming consistency.
* Make sure that when a run already has log, it is updated (before it would
  hang on the database integrity error).


v1.2.1
~~~~~~

* Make the worker crash early instead of hanging on errors happening before the
  actual job starts, to give the user a visible cue that something went wrong.


v1.2.0
~~~~~~

* The worker will now terminate gracefully when receiving the ``TERM`` signal.
  This means that all pending jobs will be completed, but that it will not
  accept any new jobs. After finishing the last pending job, the worker will
  terminate.


v1.1.4
~~~~~~

* Set ``reconnect_after_inactivity`` default to 10 minutes. This is 2 x the
  ``JOB_RUNNER_WORKER_PING_INTERVAL`` default setting in Job-Runner.


v1.1.3
~~~~~~

* Implement handler for ``ping`` action.


v1.1.2
~~~~~~

* Add and implement ``reconnect_after_inactivity`` setting.


v1.1.1
~~~~~~

* Run script by finding their shebang without the x bit being needed.


v1.1.0
~~~~~~

* Handle separate run log-output resource. This requires Job-Runner >= v1.3.0.


v1.0.7
~~~~~~

* Fix killing job-runs. Where *v1.0.5* was killing children processes, it did
  not kill children of children, ... This should kill the full tree of
  child-processes.


v1.0.6
~~~~~~

* Freeze requests library version, since 1.0.0 contains backwards compatible
  changes.


v1.0.5
~~~~~~

* Fix killing job-runs. When the process had sub-processes, only the parent
  process was killed and the worker was waiting for the child-processes to
  complete.


v1.0.4
~~~~~~

* Add config variable ``max_log_bytes`` to limit the amount of logdata that
  will be send back to the API (to avoid ``413 Request Entity Too Large``
  errors).


v1.0.3
~~~~~~

* Send ``pid`` back to the REST API when a job has been started.
* Kill a job-run when a ``kill`` action is received.


v1.0.2
~~~~~~

* Make sure that the API exactly matches.


v1.0.1
~~~~~~

* Make the timezones send to the REST API timezone aware.


v1.0.0
~~~~~~

* Deployar related changes.


v0.7.1
~~~~~~

* Fix encoding issue when writing the file.


v0.7.0
~~~~~~

* Refactor to make the worker compatible with the 0.7 version of the
  ``job-runner`` package.
* Make it consume runs from the queue broadcaster instead of hitting the REST
  interface every x seconds.
* Add retry on error to recover from temporary REST interface errors.


v0.6.1
~~~~~~

* Merge fixes v0.5.1 and v0.5.2 into v0.6.x version.


v0.6.0
~~~~~~

* Refactor to make use of separate WebSocket Server.


v0.5.2
~~~~~~

* Make temporary path for scripts configurable.


v0.5.1
~~~~~~

* Disable SSL certificate validation.


v0.5.0
~~~~~~

* Initial release.
