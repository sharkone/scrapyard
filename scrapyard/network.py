import cache
import feedparser
import json
import requests
import sys
import timeit

################################################################################
TIMEOUT = 20

################################################################################
# HTTP
################################################################################
def http_get(url, params={}, headers={}, timeout=TIMEOUT, logging=True):
    start_time = timeit.default_timer()

    request = requests.Request('GET', url, params=params, headers=headers)
    request = request.prepare()

    try:
        session  = requests.Session()
        response = session.send(request, timeout=timeout)
        response.raise_for_status()
        if logging:
            sys.stdout.write('-> {0} : {1:4.2f}s : {2}\n'.format('NET', timeit.default_timer() - start_time, request.url))
        return response.content
    except requests.exceptions.RequestException as exception:
        if logging:
            sys.stderr.write('-> {0} : {1:4.2f}s : {2} : {3}\n'.format('ERR', timeit.default_timer() - start_time, request.url, repr(exception).replace(',)', ')')))
        raise exception

################################################################################
def http_get_cached_mandatory(url, expiration, retry_delay=1, max_retries=20, params={}, headers={}, timeout=TIMEOUT):
    return cache.mandatory(http_get, expiration=expiration, retry_delay=retry_delay, max_retries=max_retries)(url, params=params, headers=headers, timeout=timeout)

################################################################################
def http_get_cached_optional(url, expiration, params={}, headers={}, timeout=TIMEOUT):
    return cache.optional(http_get, expiration=expiration)(url, params=params, headers=headers, timeout=timeout)

################################################################################
# JSON
################################################################################
def json_get(url, params={}, headers={}, timeout=TIMEOUT):
    return json.loads(http_get(url, params=params, headers=headers, timeout=timeout))

################################################################################
def json_get_cached_mandatory(url, expiration, retry_delay=1, max_retries=20, params={}, headers={}, timeout=TIMEOUT):
    return cache.mandatory(json_get, expiration=expiration, retry_delay=retry_delay, max_retries=max_retries)(url, params=params, headers=headers, timeout=timeout)

################################################################################
def json_get_cached_optional(url, expiration, params={}, headers={}, timeout=TIMEOUT):
    return cache.optional(json_get, expiration=expiration)(url, params=params, headers=headers, timeout=timeout)

################################################################################
# RSS
################################################################################
def rss_get(url, params={}, headers={}, timeout=TIMEOUT):
    return feedparser.parse(http_get(url, params=params, headers=headers, timeout=timeout))

################################################################################
def rss_get_cached_mandatory(url, expiration, retry_delay=1, max_retries=20, params={}, headers={}, timeout=TIMEOUT):
    return cache.mandatory(rss_get, expiration=expiration, retry_delay=retry_delay, max_retries=max_retries)(url, params=params, headers=headers, timeout=timeout)

################################################################################
def rss_get_cached_optional(url, expiration, params={}, headers={}, timeout=TIMEOUT):
    return cache.optional(rss_get, expiration=expiration)(url, params=params, headers=headers, timeout=timeout)
