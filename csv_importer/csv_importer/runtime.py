"""
In this file is kept the runtime state for the current execution of the
CLI application or given DAG. This includes:
* is the execution a dry run
* is verbose logging enabled

Here is also implemented custom VerboseLogger logging sub-class which
is used by the CLI app and the DAGs.
It respects the current state of is_verbose().
"""

import logging
import sys
import os

from functools import cache
from datetime import datetime
from zoneinfo import ZoneInfo


# These two variables keep the state of the current execution of the
# application or DAG.
_verbose = False
_dry_run = False

_now = datetime.now(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H-%M-%S')


def enable_verbose_logging():
    global _verbose
    _verbose = True


def is_verbose() -> bool:
    return _verbose


def enable_dry_run():
    global _dry_run
    _dry_run = True


def is_dry_run() -> bool:
    return _dry_run


@cache
def edit_stamp() -> str:
    user = os.environ.get('USER', 'unknown')
    airflow_run_id = os.environ.get('AIRFLOW_CTX_DAG_RUN_ID')
    if airflow_run_id:
        return f'{airflow_run_id}-{user}'
    else:
        return f'{_now}-{user}'


class VerboseLogger(logging.getLoggerClass()):
    """
    Subclass of Logger with method which will print conditionally at
    INFO level.
    This is needed, because when the module is executed as DAG, we cannot
    change the log level configured in Airflow cfg file. By default
    Airflow works with INFO logging level.
    """
    def verbose_info(self, *args, **kwargs):
        """
        Logs at info level (the default Airflow logging level) but conditionally
        based on the is_verbose() result.
        """
        if is_verbose():
            self.info(*args, **kwargs)


logging.setLoggerClass(VerboseLogger)


def getLogger(name: str) -> VerboseLogger:
    l = logging.getLogger(name)
    if not isinstance(l, VerboseLogger):
        print(
            f'Logger {l.name} is of type {type(l)}, while it should be of VerboseLogger.',
            file=sys.stderr
        )

    return l
