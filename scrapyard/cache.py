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

TIMEOUT_TOTAL = 20

redis_url  = urlparse.urlparse(os.getenv('REDISCLOUD_URL', 'redis://{0}:{1}'.format(os.getenv('IP', '0.0.0.0'), 6379)))
redis_pool = redis.ConnectionPool(max_connections=10, host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

################################################################################
def __get(key):
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

################################################################################
def __set(key, value, expiration=None):
    start_time = timeit.default_timer()
    try:
        redis_cache = redis.StrictRedis(connection_pool=redis_pool)
        value = pickle.dumps(value)
        value = zlib.compress(value, 9)

        if expiration:
            redis_cache.setex(key, int(expiration.total_seconds()), value)
        else:
            redis_cache.set(key, value)
        # sys.stdout.write('RDS:SUC : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
    except redis.exceptions.RedisError as exception:
        sys.stderr.write('RDS:ERR : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))
        raise exception

################################################################################
def cache(key, init_func, init_exception_handler, init_failure_handler, update_func, data_expiration, cache_expiration=WEEK):
    start_time = timeit.default_timer()
    value      = __get(key)

    if not value:
        func_result = None
        while (timeit.default_timer() - start_time) < TIMEOUT_TOTAL:
            try:
                func_result = { 'expires_on': datetime.datetime.utcnow() + data_expiration, 'data': init_func() }
                __set(key, func_result, cache_expiration)
                sys.stdout.write('DAT:NEW : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
                return func_result['data']
            except Exception as exception:
                if init_exception_handler:
                    init_exception_handler(exception)
        sys.stderr.write('DAT:ERR : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
        if init_failure_handler:
            init_failure_handler()
    else:
        if value['expires_on'] > datetime.datetime.now():
            # Cache valid
            sys.stdout.write('DAT:HIT : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
            return value['data']
        else:
            # Cache expired, quickly try to update it, return cached data on failure
            try:
                func_result = { 'expires_on': datetime.datetime.utcnow() + data_expiration, 'data': update_func() }
                __set(key, func_result, cache_expiration)
                sys.stdout.write('DAT:EXP : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
                return func_result['data']
            except Exception as exception:
                sys.stderr.write('DAT:FLB : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))
                return value['data']

################################################################################
def cache_optional(key, update_func, data_expiration, cache_expiration=WEEK):
    start_time = timeit.default_timer()
    value      = __get(key)

    if value == None or value['expires_on'] <= datetime.datetime.now():
        # Cache expired, quickly try to update it, return cached data on failure if available
        try:
            func_result = { 'expires_on': datetime.datetime.utcnow() + data_expiration, 'data': update_func() }
            __set(key, func_result, cache_expiration)
            sys.stdout.write('DAT:{0} : {1:3.1f}s : {2}\n'.format('EXP' if value else 'NEW', timeit.default_timer() - start_time, key))
            return func_result['data']
        except Exception as exception:
            if value:
                sys.stderr.write('DAT:FLB : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))
                return value['data']
            sys.stderr.write('DAT:ERR : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, key, repr(exception).replace(',)', ')')))
    else:
        # Cache valid
        sys.stdout.write('DAT:HIT : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, key))
        return value['data']
