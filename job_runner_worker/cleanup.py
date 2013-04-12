import logging

from job_runner_worker.config import config
from job_runner_worker.models import Run


logger = logging.getLogger(__name__)


def reset_incomplete_runs():
    """
    Cleanup incomplete runs.

    A run is left incomplete when a worker dies while the run hasn't been
    finished (or was marked as enqueued). These runs needs to be re-started
    and therefore reset to scheduled state.

    """
    logger.info('Cleaning up incomplete runs')
    incomplete_runs = []

    for state in ['in_queue', 'started']:
        incomplete_runs.extend(Run.get_list(
            config.get('job_runner_worker', 'run_resource_uri'),
            params={
                'state': state,
                'worker__api_key': config.get('job_runner_worker', 'api_key'),
            }
        ))

    for run in incomplete_runs:
        logger.warning('Run {0} was left incomplete'.format(run.resource_uri))
        run.patch({
            'enqueue_dts': None,
            'start_dts': None,
        })
