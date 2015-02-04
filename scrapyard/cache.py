import datetime
import os
import pickle
import redis
import sys
import timeit
import urlparse

HOUR = datetime.timedelta(hours=1)
DAY  = datetime.timedelta(days=1)
WEEK = datetime.timedelta(days=1)

redis_url        = urlparse.urlparse(os.getenv('REDISCLOUD_URL', 'redis://{0}:{1}'.format(os.getenv('IP', '0.0.0.0'), 6379)))
redis_pool       = redis.ConnectionPool(max_connections=10, host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

def get(key):
    start_time = timeit.default_timer()
    try:
        redis_cache = redis.StrictRedis(connection_pool=redis_pool)
        result = redis_cache.get(key)
        result = pickle.loads(result) if result else result
        # sys.stdout.write('{0} : {1:3.1f}s : GET : {2}\n'.format('RDS:OK', timeit.default_timer() - start_time, key))
        return result
    except redis.exceptions.RedisError as exception:
        sys.stderr.write('{0} : {1:3.1f}s : GET : {2} : {3}\n'.format('RDS:KO', timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))

def set(key, value):
    start_time = timeit.default_timer()
    try:
        redis_cache = redis.StrictRedis(connection_pool=redis_pool)
        redis_cache.set(key, pickle.dumps(value))
        # sys.stdout.write('{0} : {1:3.1f}s : SET : {2}\n'.format('RDS:OK', timeit.default_timer() - start_time, key))
    except redis.exceptions.RedisError as exception:
        sys.stderr.write('{0} : {1:3.1f}s : SET : {2} : {3}\n'.format('RDS:KO', timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))
