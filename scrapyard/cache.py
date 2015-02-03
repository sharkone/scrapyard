import datetime
import decorator
import hashlib
import os
import pickle
import redis
import sys
import timeit
import urlparse

HOUR = datetime.timedelta(hours=1)
DAY  = datetime.timedelta(days=1)
WEEK = datetime.timedelta(days=1)

redis_url = urlparse.urlparse(os.getenv('REDISCLOUD_URL', 'redis://{0}:{1}'.format(os.getenv('IP', '0.0.0.0'), 6379)))

def __get_cache(key):
    start_time = timeit.default_timer()
    try:
        redis_cache = redis.StrictRedis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)
        result = redis_cache.get(key)
        result = pickle.loads(result) if result else result
        # sys.stdout.write('{0} : {1:3.1f}s : GET : {2}\n'.format('RDS:OK', timeit.default_timer() - start_time, key))
        return result
    except redis.exceptions.RedisError as exception:
        sys.stderr.write('{0} : {1:3.1f}s : GET : {2} : {3}\n'.format('RDS:KO', timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))

def __set_cache(key, expiration, value):
    start_time = timeit.default_timer()
    try:
        redis_cache = redis.StrictRedis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)
        redis_cache.setex(key, int(expiration.total_seconds()), pickle.dumps(value))
        # sys.stdout.write('{0} : {1:3.1f}s : SET : {2}\n'.format('RDS:OK', timeit.default_timer() - start_time, key))
    except redis.exceptions.RedisError as exception:
        sys.stderr.write('{0} : {1:3.1f}s : SET : {2} : {3}\n'.format('RDS:KO', timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))

def cache(func, expiration, cache_key=None):
    def _cache(func, *args, **kwargs):
        key   = hashlib.md5(':'.join([func.__name__, str(args), str(kwargs)])).hexdigest() if not cache_key else cache_key
        value = __get_cache(key)

        # Update if needed
        if not value or value['expires_on'] < datetime.datetime.now():
            data = func(*args, **kwargs)
            if data:
                value = { 'expires_on': datetime.datetime.now() + expiration, 'data': data }
                __set_cache(key, expiration, value)

        # Return what we got
        return value['data'] if value else None

    return decorator.decorator(_cache, func)
