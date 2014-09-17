import logging
from twisted.python import log


def start_log(level=logging.INFO):
    observer = logger(level)
    log.startLoggingWithObserver(observer)


def logger(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(
        format='%(asctime)s-[%(levelname)s]-%(name)s :  %(message)s',
        level=numeric_level)
    observer = log.PythonLoggingObserver()
    return observer.emit
