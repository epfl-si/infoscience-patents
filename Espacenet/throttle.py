# -*- coding: utf-8 -*-

"""
    (c) All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2017
"""

from datetime import timedelta
from time import time, sleep
from functools import wraps

import logging

logger = logging.getLogger(__file__)

class throttle(object):
    def __init__(self, limit, interval):
        self.limit = limit
        
        if not isinstance(interval, timedelta):
            raise ValueError("interval is not a timedelta")
        
        # timedelta.total_seconds doesn't exit in 2.6 ... 
        self._total_seconds = (interval.microseconds + (interval.seconds + interval.days * 24.0 * 3600.0) * 10**6) / 10**6
        
        self._times = []
    
    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = time()
            self._times.append(now)
            
            # remove entries older than the interval
            self._times = filter(lambda t: t > (now-self._total_seconds), self._times)
            
            if len(self._times) >= self.limit:
                # wait the appropriate amount of time before calling fn
                sleep_time = self._total_seconds - (now-self._times[0])
                logger.info("Waiting %s sec" % sleep_time)
                sleep(sleep_time)
            
            return fn(*args, **kwargs)
        
        return wrapper

#===============================================================================
# @throttle(2, timedelta(seconds=1))
# def do_something(i):
#     sleep(0.1)
#     print "something #", i
# 
# n = 0
# start = time()
# for i in range(10):
#     print "trying to call do_something", i+1
#     do_something(i+1)
#     n += 1
# end = time()
# 
# print 
# print "called %s in %s" % (n, end-start)
#===============================================================================