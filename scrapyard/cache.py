import datetime
import decorator
import hashlib
import os
import pickle
import redis
import time
import urlparse

HOUR = datetime.timedelta(hours=1)
DAY  = datetime.timedelta(days=1)
WEEK = datetime.timedelta(days=1)

redis_url   = urlparse.urlparse(os.getenv('REDISCLOUD_URL', 'redis://{0}:{1}'.format(os.getenv('IP', '0.0.0.0'), 6379)))
redis_cache = redis.StrictRedis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

def optional(func, expiration):
    def _optional(func, *args, **kwargs):
        key   = hashlib.md5(':'.join([func.__name__, str(args), str(kwargs)])).hexdigest()
        value = redis_cache.get(key)

        # Update if needed
        value = pickle.loads(value) if value else value
        if not value or value['expires_on'] < datetime.datetime.now():
            data = func(*args, **kwargs)
            if data:
                value = { 'expires_on': datetime.datetime.now() + expiration, 'data': data }
                redis_cache.setex(key, int(expiration.total_seconds()), pickle.dumps(value))

        # Return what we got
        return value['data'] if value else None

    return decorator.decorator(_optional, func)

def mandatory(func, expiration, retry_delay, max_retries):
    def _mandatory(func, *args, **kwargs):
        key   = hashlib.md5(':'.join([func.__name__, str(args), str(kwargs)])).hexdigest()
        value = redis_cache.get(key)

        # Force initial update
        if not value:
            retry_count = max_retries
            while retry_count > 0:
                data = func(*args, **kwargs)
                if data:
                    value = { 'expires_on' : datetime.datetime.now() + expiration, 'data': data }
                    redis_cache.setex(key, int(expiration.total_seconds()), pickle.dumps(value))
                    break
                time.sleep(retry_delay)
                retry_count -= 1
        else:
            # Update if needed
            value = pickle.loads(value)
            if value['expires_on'] < datetime.datetime.now():
                data = func(*args, **kwargs)
                if data:
                    value = { 'expires_on': datetime.datetime.now() + expiration, 'data': data }
                    redis_cache.setex(key, int(expiration.total_seconds()), pickle.dumps(value))

        # Return what we got
        return value['data'] if value else None

    return decorator.decorator(_mandatory, func)
