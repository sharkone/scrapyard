import cache
import feedparser
import json
import requests
import retrying
import sys
import timeit

################################################################################
TIMEOUT = 10

################################################################################
# HTTP
################################################################################
def __retry_on_exception(exception):
    if isinstance(exception, requests.exceptions.HTTPError) and exception.response.status_code == 404:
        return False
    return isinstance(exception, requests.exceptions.RequestException)

################################################################################
@retrying.retry(wait_fixed=1000, stop_max_delay=10000, retry_on_exception=__retry_on_exception)
def __http_get_retry(request, timeout=TIMEOUT, logging=True):
    return __http_get(request, timeout, logging)

################################################################################
def __http_get(request, timeout=TIMEOUT, logging=True):
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
def http_get(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    request = requests.Request('GET', url, params=params, headers=headers)
    request = request.prepare()
    return __http_get(request, timeout, logging)

################################################################################
def http_get_cached(url, expiration, params={}, headers={}, timeout=TIMEOUT, logging=True):
    request = requests.Request('GET', url, params=params, headers=headers)
    request = request.prepare()
    return cache.cache(__http_get, expiration, request.url)(request, timeout, logging)

################################################################################
def http_get_retry(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    request = requests.Request('GET', url, params=params, headers=headers)
    request = request.prepare()
    return __http_get_retry(request, timeout, logging)

################################################################################
def http_get_retry_cached(url, expiration, params={}, headers={}, timeout=TIMEOUT, logging=True):
    request = requests.Request('GET', url, params=params, headers=headers)
    request = request.prepare()
    return cache.cache(__http_get_retry, expiration, request.url)(request, timeout, logging)

################################################################################
# JSON
################################################################################
def json_get(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get(url, params, headers, timeout, logging)
    return json.loads(data) if data else data

################################################################################
def json_get_cached(url, expiration, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get_cached(url, expiration, params, headers, timeout, logging)
    return json.loads(data) if data else data

################################################################################
def json_get_retry(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get_retry(url, params, headers, timeout, logging)
    return json.loads(data) if data else data

################################################################################
def json_get_retry_cached(url, expiration, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get_retry_cached(url, expiration, params, headers, timeout, logging)
    return json.loads(data) if data else data

################################################################################
# RSS
################################################################################
def rss_get(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get(url, params, headers, timeout, logging)
    return feedparser.parse(data) if data else data

################################################################################
def rss_get_cached(url, expiration, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get_cached(url, expiration, params, headers, timeout, logging)
    return feedparser.parse(data) if data else data

################################################################################
def rss_get_retry(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get_retry(url, params, headers, timeout, logging)
    return feedparser.parse(data) if data else data

################################################################################
def rss_get_retry_cached(url, expiration, params={}, headers={}, timeout=TIMEOUT, logging=True):
    data = http_get_retry_cached(url, expiration, params, headers, timeout, logging)
    return feedparser.parse(data) if data else data
