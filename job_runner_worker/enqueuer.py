import logging
import json
import time
from datetime import datetime

from job_runner_worker.config import config
from job_runner_worker.models import RestError, Run


logger = logging.getLogger(__name__)


def enqueue_runs(run_queue, event_queue):
    """
    Populate the ``run_queue``.

    :param run_queue:
        An instance of ``Queue`` for pushing the runs to.

    :param event_queue:
        An instance of ``Queue`` for pushing events to.

    """
    while True:
        if not run_queue.full():
            try:
                runs = Run.get_list(
                    config.get('job_runner_worker', 'run_resource_uri'),
                    params={
                        'limit': 1,
                        'state': 'scheduled',
                        'schedule_dts__lte': datetime.utcnow().isoformat(' '),
                    }
                )

                if len(runs):
                    run = runs[0]
                    run.patch({
                        'enqueue_dts': datetime.utcnow().isoformat(' ')
                    })
                    run_queue.put(run)
                    event_queue.put(json.dumps(
                        {'event': 'enqueued', 'run_id': run.id}))
                else:
                    time.sleep(5)

            except RestError:
                logger.exception(
                    'An exception was raised while populating the queue')
                time.sleep(5)
        else:
            time.sleep(5)
