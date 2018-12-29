import time
import logging

DEBUG = False


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result
    return timed


def logger(func):
    def wrapper(self, *argv, **kwargv):
        if DEBUG:
            logging.basicConfig(filename='myapp.log', level=logging.INFO)
            logging.info(func.__doc__)
        return func(self, *argv, **kwargv)
    return wrapper
