import codecs
import json
import logging
import os
import tempfile
from datetime import datetime

import gevent_subprocess as subprocess

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
    logger.info('Started run executer')

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

        run.patch({
            'start_dts': datetime.utcnow().isoformat(' ')
        })
        event_queue.put(json.dumps({'event': 'started', 'run_id': run.id}))

        logger.info('Starting run {0}'.format(run.resource_uri))
        sub_proc = subprocess.Popen(
            [file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sub_proc.communicate()
        logger.info('Run {0} ended'.format(run.resource_uri))

        run.patch({
            'return_dts': datetime.utcnow().isoformat(' '),
            'return_log': '{0}{1}'.format(out, err),
            'return_success': False if sub_proc.returncode else True,
        })
        event_queue.put(json.dumps({'event': 'returned', 'run_id': run.id}))
        os.remove(file_path)
