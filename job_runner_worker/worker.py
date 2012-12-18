import codecs
import json
import logging
import os
import signal
import tempfile
from datetime import datetime

import gevent_subprocess as subprocess
from pytz import utc

from job_runner_worker.config import config


logger = logging.getLogger(__name__)


def execute_run(run_queue, event_queue):
    """
    Execute runs from the ``run_queue``.

    :param run_queue:
        An instance of ``Queue`` to consume run instances from.

    :param event_queue:
        An instance of ``Queue`` to push events to.

    """
    logger.info('Starting run executer')

    for run in run_queue:

        file_desc, file_path = tempfile.mkstemp(
            dir=config.get('job_runner_worker', 'script_temp_path')
        )
        # seems there isn't support to open file descriptors directly in
        # utf-8 encoding
        os.fdopen(file_desc).close()

        file_obj = codecs.open(file_path, 'w', 'utf-8')
        os.chmod(file_path, 0700)
        file_obj.write(run.job.script_content.replace('\r', ''))
        file_obj.close()

        logger.info('Starting run {0}'.format(run.resource_uri))
        sub_proc = subprocess.Popen(
            [file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        run.patch({
            'start_dts': datetime.now(utc).isoformat(' '),
            'pid': sub_proc.pid,
        })
        event_queue.put(json.dumps(
            {'event': 'started', 'run_id': run.id, 'kind': 'run'}))

        out, err = sub_proc.communicate()
        log_output = _truncate_log('{0}{1}'.format(out, err))

        logger.info('Run {0} ended'.format(run.resource_uri))
        run.patch({
            'return_dts': datetime.now(utc).isoformat(' '),
            'return_log': log_output,
            'return_success': False if sub_proc.returncode else True,
        })
        event_queue.put(json.dumps(
            {'event': 'returned', 'run_id': run.id, 'kind': 'run'}))
        os.remove(file_path)


def kill_run(kill_queue, event_queue):
    """
    Execute kill-requests from the ``kill_queue``.

    :param kill_queue:
        An instance of ``Queue`` to consume kill-requests from.

    :param event_queue:
        An instance of ``Queue`` to push events to.

    """
    logger.info('Starting executor for kill-requests')

    for kill_request in kill_queue:
        run = kill_request.run

        _kill_pid_tree(run.pid)
        kill_request.patch({'execute_dts': datetime.now(utc).isoformat(' ')})
        event_queue.put(json.dumps({
            'event': 'executed',
            'kill_request_id': kill_request.id,
            'kind': 'kill_request'
        }))


def _kill_pid_tree(pid):
    """
    Kill a given ``pid`` including its tree of children.

    :param pid:
        An ``int`` representing the parent ``PID``.

    """
    children = _get_child_pids(pid)
    for child_pid in children:
        _kill_pid_tree(child_pid)
    os.kill(pid, signal.SIGKILL)


def _get_child_pids(pid):
    """
    Return the list of children ``PID``s for the given parent ``pid``.

    :param pid:
        An ``int`` representing the parent ``PID``.

    :return:
        A ``list`` of children ``PIDS``s (if any).

    """
    sub_proc = subprocess.Popen(
        ['ps', '-o', 'pid', '--ppid', str(pid), '--noheaders'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ret_code = sub_proc.wait()

    if ret_code == 0:
        out, err = sub_proc.communicate()
        return [int(x) for x in out.split('\n')[:-1]]

    return []


def _truncate_log(log_txt):
    """
    Truncate the ``log_txt`` in case it exeeds the max. log size.

    :param log_txt:
        A ``str``.

    """
    max_log_bytes = config.getint('job_runner_worker', 'max_log_bytes')

    if len(log_txt) > max_log_bytes:
        top_length = int(max_log_bytes * 0.2)
        bottom_length = int(max_log_bytes * 0.8)

        log_txt = '{0}\n\n[truncated]\n\n{1}'.format(
            log_txt[:top_length],
            log_txt[len(log_txt) - bottom_length:]
        )

    return log_txt
