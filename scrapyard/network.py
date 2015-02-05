import cache
import datetime
import exceptions
import feedparser
import json
import requests
import sys
import time
import timeit

################################################################################
TIMEOUT_CONNECT = 1
TIMEOUT_READ    = 20
TIMEOUT_TOTAL   = 20

################################################################################
# HTTP
################################################################################
def __http_get(request, timeout):
    start_time = timeit.default_timer()
    try:
        session  = requests.Session()
        response = session.send(request, timeout=timeout)
        response.raise_for_status()
        # sys.stdout.write('NET:SUC : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, request.url))
        return response.content
    except requests.exceptions.RequestException as exception:
        sys.stderr.write('NET:ERR : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, request.url, repr(exception).replace(',)', ')')))
        raise exception

################################################################################
def http_get(url, expiration, cache_expiration=cache.WEEK, params={}, headers={}):
    start_time  = timeit.default_timer()

    request      = requests.Request('GET', url, params=params, headers=headers).prepare()
    cache_result = cache.get(request.url)

    if not cache_result:
        http_result = None
        while (timeit.default_timer() - start_time) < TIMEOUT_TOTAL:
            try:
                http_result = { 'expires_on': datetime.datetime.now() + expiration, 'data': __http_get(request, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ)) }
                cache.set(request.url, http_result)
                sys.stderr.write('DAT:NEW : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, request.url))
                return http_result['data']
            except requests.exceptions.HTTPError as exception:
                if exception.response.status_code == 404:
                    # Give up right away
                    raise exceptions.HTTPError(404)
                # Retry after delay
                time.sleep(1)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                # Retry right away
                pass
        sys.stderr.write('DAT:ERR : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, request.url))
        raise exceptions.HTTPError(503)
    else:
        if cache_result['expires_on'] > datetime.datetime.now():
            # Cache valid
            sys.stdout.write('DAT:HIT : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, request.url))
            return cache_result['data']
        else:
            # Cache expired, quickly try to update it, return cached data on failure
            try:
                http_result = { 'expires_on': datetime.datetime.now() + expiration, 'data': http_get(request, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ)) }
                cache.set(request.url, http_result, cache_expiration)
                sys.stdout.write('DAT:EXP : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, request.url))
                return http_result['data']
            except Exception:
                sys.stderr.write('DAT:FLB : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, request.url, repr(exception).replace(',)', ')')))
                return cache_result['data']

################################################################################
def __http_get_old(request, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ)):
    start_time = timeit.default_timer()
    try:
        session  = requests.Session()
        response = session.send(request, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as exception:
        raise exception

################################################################################
def http_get_old(url, params={}, headers={}, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ)):
    request = requests.Request('GET', url, params=params, headers=headers)
    request = request.prepare()
    return __http_get_old(request, timeout)

################################################################################
# JSON
################################################################################
def json_get(url, expiration, cache_expiration=cache.WEEK, params={}, headers={}):
    http_data = http_get(url, expiration, cache_expiration=cache_expiration, params=params, headers=headers)
    try:
        return json.loads(http_data)
    except ValueError:
        raise exceptions.HTTPError(404)

################################################################################
# RSS
################################################################################
def rss_get(url, expiration, cache_expiration=cache.WEEK, params={}, headers={}):
    return feedparser.parse(http_get(url, expiration, cache_expiration=cache_expiration, params=params, headers=headers))
