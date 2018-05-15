# Copyright (c) 2018 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import os
import errno
import json
import argparse
import logging
from contextlib import contextmanager


def _mkdir_p(path):
    """"Create a directory at 'path', ignore if the directory already exists.

    Needed, because the 'ignore_exists' is not available in Python 2.7.
    """
    try:
        os.makedirs(path)
    except OSError as error:
        if not (error.errno == errno.EEXIST and os.path.isdir(path)):
            raise


def _positive_int(value):
    """Expect a command line argument to be a positive integer.

    Designed to be used in conjunction with an argparse.ArgumentParser.

    :param value:
        This function will raise an argparse.ArgumentTypeError if value
        is not a positive integer.
    :raises:
        :class:`argparse.ArgumentTypeError`
    """
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError("Value must be positive.")
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(
            "{} must be a positive integer.".format(value))
    return ivalue


def draw_progressbar(value, total, width=40):
    """Visualize progess with a progress bar.

    :param value:
        The current progress as a fraction of total.
    :type value:
        int
    :param total:
        The maximum value that 'value' may obtain.
    :type total:
        int
    :param width:
        The character width of the drawn progress bar.
    :type width:
        int
    """
    "Helper function for the visualization of progress."
    assert value >= 0 and total > 0
    n = int(value / total * width)
    return '|' + ''.join(['#'] * n) + ''.join(['-'] * (width - n)) + '|'


def _identical(iterator):
    """Check that all elements of an iterator are identical"""
    return len(set(iterator)) <= 1


def _format_timedelta(delta):
    "Format a time delta for interpretation by schedulers."
    if isinstance(delta, int) or isinstance(delta, float):
        import datetime
        delta = datetime.timedelta(hours=delta)
    hours, r = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(r, 60)
    hours += delta.days * 24
    return "{:0>2}:{:0>2}:{:0>2}".format(hours, minutes, seconds)


def write_human_readable_statepoint(script, job):
    """Human-readable representation of a signac state point."""
    script.write('# Statepoint:\n#\n')
    sp_dump = json.dumps(job.statepoint(), indent=2).replace(
        '{', '{{').replace('}', '}}')
    for line in sp_dump.splitlines():
        script.write('# ' + line + '\n')


@contextmanager
def redirect_log(job, filename='run.log', formatter=None, logger=None):
    """Redirect all messages logged via the logging interface to the given file.

    :param job:
        An instance of a signac job.
    :type job:
        :class:`signac.Project.Job`
    :formatter:
        The logging formatter to use, uses a default formatter if this argument
        is not provided.
    :type formatter:
        :class:`logging.Formatter`
    :param logger:
        The instance of logger to which the new file log handler is added. Defaults
        to the default logger returned by `logging.getLogger()` if this argument is
        not provided.
    type logger:
        :class:`logging.Logger`
    """
    if formatter is None:
        formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    if logger is None:
        logger = logging.getLogger()

    filehandler = logging.FileHandler(filename=job.fn('run.log'))
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    try:
        yield
    finally:
        logger.removeHandler(filehandler)


@contextmanager
def add_path_to_environment_pythonpath(path):
    "Temporarily insert the current working directory into the environment PYTHONPATH variable."
    path = os.path.realpath(path)
    pythonpath = os.environ.get('PYTHONPATH')
    if pythonpath:
        for path_ in pythonpath:
            if os.path.isabs(path_) and os.path.realpath(path_) == path:
                yield   # Path is already in PYTHONPATH, nothing to do here.
                return
        try:
            # Append the current working directory to the PYTHONPATH.
            tmp_path = [path] + pythonpath.split(':')
            os.environ['PYTHONPATH'] = ':'.join(tmp_path)
            yield
        finally:
            os.environ['PYTHONPATH'] = pythonpath
            pass
    else:
        try:
            # The PYTHONPATH was previously not set, set to current working directory.
            os.environ['PYTHONPATH'] = path
            yield
        finally:
            del os.environ['PYTHONPATH']


@contextmanager
def add_cwd_to_environment_pythonpath():
    with add_path_to_environment_pythonpath(os.getcwd()):
        yield


@contextmanager
def switch_to_directory(root=None):
    "Temporarily switch into the given root directory (if not None)."
    if root is None:
        yield
    else:
        cwd = os.getcwd()
        try:
            os.chdir(root)
            yield
        finally:
            os.chdir(cwd)
