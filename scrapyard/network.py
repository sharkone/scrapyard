import cache
import exceptions
import feedparser
import functools
import json
import requests
import sys
import time
import timeit

################################################################################
TIMEOUT_CONNECT = 2
TIMEOUT_READ    = 20

################################################################################
# HTTP
################################################################################
def __http_get(request, timeout, log_success=True, log_failure=True):
    start_time = timeit.default_timer()
    try:
        session  = requests.Session()
        response = session.send(request, timeout=timeout)
        response.raise_for_status()
        if log_success:
            sys.stdout.write('NET:HIT : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, request.url))
        return response.content
    except requests.exceptions.RequestException as exception:
        if log_failure:
            sys.stderr.write('NET:ERR : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, request.url, repr(exception).replace(',)', ')')))
        raise exception

################################################################################
def http_get_init_exception_handler(exception):
    if isinstance(exception, requests.exceptions.HTTPError):
        if exception.response.status_code == 404:
            # Give up right away
            raise exceptions.HTTPError(404)
        # Retry after delay
        time.sleep(1)
        return
    elif isinstance(exception, requests.exceptions.ConnectionError) or isinstance(exception, requests.exceptions.Timeout):
        # Retry right away
        return

    raise exception

################################################################################
def http_get_init_failure_handler():
    raise exceptions.HTTPError(503)

################################################################################
def http_get(url, params={}, headers={}, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ), logging=True):
    request = requests.Request('GET', url, params=params, headers=headers).prepare()
    return __http_get(request, timeout=timeout, log_success=logging, log_failure=logging)

################################################################################
# JSON
################################################################################
def json_get(url, params={}, headers={}, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ), logging=True):
    start_time = timeit.default_timer()
    try:
        request   = requests.Request('GET', url, params=params, headers=headers).prepare()
        http_data = __http_get(request, timeout=timeout, log_success=False, log_failure=logging)
        json_data = json.loads(http_data)
        if logging:
            sys.stdout.write('NET:HIT : {0:3.1f}s : {1}\n'.format(timeit.default_timer() - start_time, request.url))
        return json_data
    except ValueError as exception:
        if logging:
            sys.stderr.write('NET:ERR : {0:3.1f}s : {1} : {2}\n'.format(timeit.default_timer() - start_time, request.url, repr(exception).replace(',)', ')')))
        raise exceptions.JSONError(request.url)

################################################################################
# RSS
################################################################################
def rss_get(url, params={}, headers={}, timeout=(TIMEOUT_CONNECT, TIMEOUT_READ), logging=True):
    request = requests.Request('GET', url, params=params, headers=headers).prepare()
    http_data = __http_get(request, timeout=timeout, log_success=logging, log_failure=logging)
    return feedparser.parse(http_data)
