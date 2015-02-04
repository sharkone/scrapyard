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
TIMEOUT       = 1
TIMEOUT_TOTAL = 10

################################################################################
# HTTP
################################################################################
def __http_get(request, timeout):
    start_time = timeit.default_timer()
    try:
        session  = requests.Session()
        response = session.send(request, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as exception:
        sys.stderr.write('{0} : {1:3.1f}s : GET : {2} : {3}\n'.format('NET:KO', timeit.default_timer() - start_time, request.url, repr(exception).replace(',)', ')')))
        raise exception

################################################################################
def http_get(url, cache_expiration, params={}, headers={}):
    request      = requests.Request('GET', url, params=params, headers=headers).prepare()
    cache_result = cache.get(request.url)

    if not cache_result:
        start_time  = timeit.default_timer()
        http_result = None
        while (timeit.default_timer() - start_time) < TIMEOUT_TOTAL:
            try:
                http_result = { 'expires_on': datetime.datetime.now() + cache_expiration, 'data': __http_get(request, timeout=TIMEOUT) }
                cache.set(request.url, http_result, cache_expiration)
                return http_result['data']
            except requests.exceptions.HTTPError as exception:
                if exception.response.status_code == 404:
                    # Give up right away
                    raise exceptions.HTTPError(404)
                # Retry after delay
                time.sleep(1)
            except requests.exceptions.Timeout:
                # Retry right away
                pass
        raise exceptions.HTTPError(503)

    else:
        if cache_result['expires_on'] > datetime.datetime.now():
            # Cache valid
            return cache_result['data']
        else:
            # Cache expired, quickly try to update it, return cached data on failure
            try:
                http_result = { 'expires_on': datetime.datetime.now() + cache_expiration, 'data': http_get(request, timeout=TIMEOUT) }
                cache.set(request.url, http_result, cache_expiration)
                return http_result['data']
            except Exception:
                return cache_result['data']

################################################################################
def __http_get_old(request, timeout=TIMEOUT, logging=True):
    start_time = timeit.default_timer()
    try:
        session  = requests.Session()
        response = session.send(request, timeout=timeout)
        response.raise_for_status()
        # if logging:
        #     sys.stdout.write('{0} : {1:3.1f}s : GET : {2}\n'.format('NET:OK', timeit.default_timer() - start_time, request.url))
        return response.content
    except requests.exceptions.RequestException as exception:
        if logging:
            sys.stderr.write('{0} : {1:3.1f}s : GET : {2} : {3}\n'.format('NET:KO', timeit.default_timer() - start_time, request.url, repr(exception).replace(',)', ')')))
        raise exception

################################################################################
def http_get_old(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    request = requests.Request('GET', url, params=params, headers=headers)
    request = request.prepare()
    return __http_get_old(request, timeout, logging)

################################################################################
# JSON
################################################################################
def json_get(url, cache_expiration, params={}, headers={}):
    http_data = http_get(url, cache_expiration, params=params, headers=headers)
    try:
        return json.loads(http_data)
    except ValueError:
        raise exceptions.HTTPError(404)

################################################################################
# RSS
################################################################################
def rss_get(url, cache_expiration, params={}, headers={}):
    return feedparser.parse(http_get(url, cache_expiration, params=params, headers=headers))
