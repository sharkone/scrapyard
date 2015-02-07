import datetime
import os
import pickle
import redis
import sys
import timeit
import urlparse
import zlib

HOUR = datetime.timedelta(hours=1)
DAY  = datetime.timedelta(days=1)
WEEK = datetime.timedelta(weeks=1)

redis_url  = urlparse.urlparse(os.getenv('REDISCLOUD_URL', 'redis://{0}:{1}'.format(os.getenv('IP', '0.0.0.0'), 6379)))
redis_pool = redis.ConnectionPool(max_connections=10, host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

def get(key):
    start_time = timeit.default_timer()
    try:
        redis_cache = redis.StrictRedis(connection_pool=redis_pool)
        value = redis_cache.get(key)
        value = zlib.decompress(value) if value else value
        value = pickle.loads(value) if value else value

        # if not value:
        #     sys.stdout.write('RDS:MIS : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
        # elif 'expires_on' in value:
        #     sys.stdout.write('RDS:{0} : {1:3.1f}s : {2}\n'.format('SUC' if value['expires_on'] > datetime.datetime.now() else 'EXP', timeit.default_timer() - start_time, key))

        return value
    except redis.exceptions.RedisError as exception:
        sys.stderr.write('RDS:ERR : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))
        raise exception

def set(key, value, expiration=None):
    start_time = timeit.default_timer()
    try:
        redis_cache = redis.StrictRedis(connection_pool=redis_pool)
        value = pickle.dumps(value)
        value = zlib.compress(value, 9)

        if expiration:
            redis_cache.setex(key, int(expiration.total_seconds()), value)
        else:
            redis_cache.set(key, pickle.dumps(value))
        # sys.stdout.write('RDS:SUC : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
    except redis.exceptions.RedisError as exception:
        sys.stderr.write('RDS:ERR : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))
        raise exception
