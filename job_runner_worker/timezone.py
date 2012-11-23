from datetime import datetime

from pytz import timezone

from job_runner_worker.config import config


def get_timezone():
    """
    Return the current timezone.
    """
    return timezone(config.get('job_runner_worker', 'timezone'))


def get_tz_aware_now():
    """
    Return a timezone aware ``datetime.datetime.now``.
    """
    return datetime.now(tz=get_timezone())
