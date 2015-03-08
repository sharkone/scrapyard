import cache
import datetime
import dateutil.parser
import dateutil.tz
import exceptions
import functools
import network
import requests
import utils

TRAKT_URL     = 'https://api-v2launch.trakt.tv'
TRAKT_HEADERS = { 'content-type': 'application/json', 'trakt-api-version': '2', 'trakt-api-key': '64cf92c702ff753cc14a6d421824efcd32f22058f79bf6d637fa92e23229f35f' }

################################################################################
# Movies
################################################################################
def __movie(trakt_slug, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    json_data = network.json_get(TRAKT_URL + '/movies/' + trakt_slug, params={ 'extended': 'full,images' }, headers=TRAKT_HEADERS, timeout=timeout)
    return  {
                'trakt_slug':       json_data['ids']['slug'],
                'imdb_id':          json_data['ids']['imdb'],
                'title':            json_data['title'],
                'year':             json_data['year'],
                'overview':         json_data['overview'],
                'tagline':          json_data['tagline'],
                'thumb':            json_data['images']['poster']['full'],
                'art':              json_data['images']['fanart']['full'],
                'runtime':          (json_data['runtime'] * 60 * 1000) if json_data['runtime'] else 0,
                'genres':           [genre.capitalize() for genre in json_data['genres']],
                'rating':           json_data['rating'],
                'released':         json_data['released'],
                'certification':    json_data['certification']
            }

def __movie_people(trakt_slug, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    result = { 'cast': [], 'crew': { 'directing': [], 'production': [], 'writing': [] } }

    json_data = network.json_get(TRAKT_URL + '/movies/' + trakt_slug + '/people', params={ 'extended': 'images' }, headers=TRAKT_HEADERS, timeout=timeout)
    if 'cast' in json_data:
        for json_item in json_data['cast']:
            result['cast'].append({
                                    'name':         json_item['person']['name'],
                                    'headshot':     json_item['person']['images']['headshot']['full'],
                                    'character':    json_item['character']
                                  })

    if 'crew' in json_data:
        if 'directing' in json_data['crew']:
            for json_item in json_data['crew']['directing']:
                result['crew']['directing'].append({
                                                        'name':     json_item['person']['name'],
                                                        'headshot': json_item['person']['images']['headshot']['full'],
                                                        'job':      json_item['job']
                                                   })

        if 'production' in json_data['crew']:
            for json_item in json_data['crew']['production']:
                result['crew']['production'].append({
                                                        'name':     json_item['person']['name'],
                                                        'headshot': json_item['person']['images']['headshot']['full'],
                                                        'job':      json_item['job']
                                                    })

        if 'writing' in json_data['crew']:
            for json_item in json_data['crew']['writing']:
                result['crew']['writing'].append({
                                                    'name':     json_item['person']['name'],
                                                    'headshot': json_item['person']['images']['headshot']['full'],
                                                    'job':      json_item['job']
                                                 })

    return result

################################################################################
def movie(trakt_slug, people_needed=False):
    cache_key                    = 'movie-{0}'.format(trakt_slug)
    cache_init_func              = functools.partial(__movie, trakt_slug=trakt_slug)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__movie, trakt_slug=trakt_slug, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.WEEK

    result = cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration)

    if people_needed:
        cache_key                    = 'movie-{0}-people'.format(trakt_slug)
        cache_init_func              = functools.partial(__movie_people, trakt_slug=trakt_slug)
        cache_init_exception_handler = network.http_get_init_exception_handler
        cache_init_failure_handler   = network.http_get_init_failure_handler
        cache_update_func            = functools.partial(__movie_people, trakt_slug=trakt_slug, timeout=network.TIMEOUT_CONNECT)
        cache_data_expiration        = cache.WEEK

        result['people'] = cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration)

    return result

################################################################################
def __movies_list_page(page, page_index, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    json_data = network.json_get(TRAKT_URL + page, params={ 'page': page_index, 'limit': 31 }, headers=TRAKT_HEADERS, timeout=timeout)
    return __movie_list_parse(json_data)

################################################################################
def __movie_list_parse(json_data):
    movie_infos = []
    if json_data:
        movie_slugs = map(lambda json_item: json_item['movie']['ids']['slug'] if 'movie' in json_item else json_item['ids']['slug'], json_data)
        movie_slugs = filter(None, movie_slugs)
        movie_infos = map(lambda movie_slug: movie(movie_slug), movie_slugs) or []
    return movie_infos

################################################################################
def movies_popular(page):
    if page < 1 or page > 10:
        raise exceptions.HTTPError(404)

    cache_key                    = 'movies-popular-{0}'.format(page)
    cache_init_func              = functools.partial(__movies_list_page, page='/movies/popular', page_index=page)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__movies_list_page, page='/movies/popular', page_index=page, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.DAY
    cache_expiration             = None

    return cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration, cache_expiration)

################################################################################
def movies_trending(page):
    if page < 1 or page > 10:
        raise exceptions.HTTPError(404)

    cache_key                    = 'movies-trending-{0}'.format(page)
    cache_init_func              = functools.partial(__movies_list_page, page='/movies/trending', page_index=page)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__movies_list_page, page='/movies/trending', page_index=page, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.HOUR
    cache_expiration             = None

    return cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration, cache_expiration)

################################################################################
def __movies_search(query, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    json_data = network.json_get(TRAKT_URL + '/search', params={ 'query': query, 'type': 'movie' }, headers=TRAKT_HEADERS, timeout=timeout)
    return __movie_list_parse(json_data)

################################################################################
def movies_search(query):
    cache_key                    = 'movies-search-{0}'.format(query)
    cache_init_func              = functools.partial(__movies_search, query=query)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__movies_search, query=query, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.DAY

    return cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration)

################################################################################
def movies_watchlist(watchlist):
    movie_slugs = filter(None, watchlist)
    movie_infos = map(lambda movie_slug : movie(movie_slug), movie_slugs) or []
    return movie_infos

################################################################################
# Shows
################################################################################
def __show(trakt_slug, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    json_data = network.json_get(TRAKT_URL + '/shows/' + trakt_slug, params={ 'extended': 'full,images' }, headers=TRAKT_HEADERS, timeout=timeout)
    return  {
                'trakt_slug':       json_data['ids']['slug'],
                'imdb_id':          json_data['ids']['imdb'],
                'title':            json_data['title'],
                'year':             json_data['year'],
                'overview':         json_data['overview'],
                'studio':           json_data['network'],
                'thumb':            json_data['images']['poster']['full'],
                'art':              json_data['images']['fanart']['full'],
                'runtime':          (json_data['runtime'] * 60 * 1000) if json_data['runtime'] else 0,
                'genres':           [genre.capitalize() for genre in json_data['genres']],
                'rating':           json_data['rating'],
                'first_aired':      json_data['first_aired'],
                'certification':    json_data['certification']
            }

################################################################################
def __show_seasons(trakt_slug, show_info, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    result = []

    json_data = network.json_get(TRAKT_URL + '/shows/' + trakt_slug + '/seasons', params={ 'extended': 'full,images' }, headers=TRAKT_HEADERS, timeout=timeout)
    for json_item in json_data:
        if json_item['number'] > 0:
            result.append({
                            'show_title':       show_info['title'],
                            'season_index':     json_item['number'],
                            'title':            'Season {0}'.format(json_item['number']),
                            'overview':         json_item['overview'],
                            'episode_count':    json_item['episode_count'],
                            'thumb':            json_item['images']['poster']['full'],
                            'art':              show_info['art']
                          })

    return result

################################################################################
def show(trakt_slug, seasons_needed=False):
    cache_key                    = 'show-{0}'.format(trakt_slug)
    cache_init_func              = functools.partial(__show, trakt_slug=trakt_slug)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__show, trakt_slug=trakt_slug, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.WEEK

    result = cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration)

    if seasons_needed:
        cache_key                    = 'show-{0}-seasons'.format(trakt_slug)
        cache_init_func              = functools.partial(__show_seasons, trakt_slug=trakt_slug, show_info=result)
        cache_init_exception_handler = network.http_get_init_exception_handler
        cache_init_failure_handler   = network.http_get_init_failure_handler
        cache_update_func            = functools.partial(__show_seasons, trakt_slug=trakt_slug, show_info=result, timeout=network.TIMEOUT_CONNECT)
        cache_data_expiration        = cache.WEEK

        result['seasons'] = cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration)

    return result

################################################################################
def __show_season(trakt_slug, season_index, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    show_info     = show(trakt_slug)
    episode_infos = []

    json_data = network.json_get(TRAKT_URL + '/shows/' + trakt_slug + '/seasons/' + str(season_index), params={ 'extended': 'full,images' }, headers=TRAKT_HEADERS, timeout=timeout)
    for json_item in json_data:
        if json_item['first_aired'] and datetime.datetime.now(dateutil.tz.tzutc()) > dateutil.parser.parse(json_item['first_aired']):
            episode_infos.append({
                                    'show_title':       show_info['title'],
                                    'season_index':     json_item['season'],
                                    'episode_index':    json_item['number'],
                                    'title':            json_item['title'],
                                    'thumb':            json_item['images']['screenshot']['full'],
                                    'art':              json_item['images']['screenshot']['full'],
                                    'overview':         json_item['overview'],
                                    'rating':           json_item['rating'],
                                    'first_aired':      json_item['first_aired'],
                                 })

    return episode_infos

################################################################################
def show_season(trakt_slug, season_index):
    cache_key                    = 'show-{0}-{1}'.format(trakt_slug, season_index)
    cache_init_func              = functools.partial(__show_season, trakt_slug=trakt_slug, season_index=season_index)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__show_season, trakt_slug=trakt_slug, season_index=season_index, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.DAY

    return cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration)

################################################################################
def show_episode(trakt_slug, season_index, episode_index):
    episode_infos = show_season(trakt_slug, season_index)
    for episode_info in episode_infos:
        if episode_info['episode_index'] == episode_index:
            return episode_info
    raise exceptions.HTTPError(404)

################################################################################
def __shows_list_page(page, page_index, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    json_data = network.json_get(TRAKT_URL + page, params={ 'page': page_index, 'limit': 31 }, headers=TRAKT_HEADERS, timeout=timeout)
    return __shows_list_parse(json_data)

################################################################################
def __shows_list_parse(json_data):
    show_infos = []
    if json_data:
        show_slugs = map(lambda json_item: json_item['show']['ids']['slug'] if 'show' in json_item else json_item['ids']['slug'], json_data)
        show_slugs = filter(None, show_slugs)
        show_infos = map(lambda show_slug: show(show_slug), show_slugs) or []
    return show_infos

################################################################################
def shows_popular(page):
    if page < 1 or page > 10:
        raise exceptions.HTTPError(404)

    cache_key                    = 'shows-popular-{0}'.format(page)
    cache_init_func              = functools.partial(__shows_list_page, page='/shows/popular', page_index=page)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__shows_list_page, page='/shows/popular', page_index=page, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.DAY
    cache_expiration             = None

    return cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration, cache_expiration)

################################################################################
def shows_trending(page):
    if page < 1 or page > 10:
        raise exceptions.HTTPError(404)

    cache_key                    = 'shows-trending-{0}'.format(page)
    cache_init_func              = functools.partial(__shows_list_page, page='/shows/trending', page_index=page)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__shows_list_page, page='/shows/trending', page_index=page, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.HOUR
    cache_expiration             = None

    return cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration, cache_expiration)

################################################################################
def __shows_search(query, timeout=(network.TIMEOUT_CONNECT, network.TIMEOUT_READ)):
    json_data = network.json_get(TRAKT_URL + '/search', params={ 'query': query, 'type': 'show' }, headers=TRAKT_HEADERS, timeout=timeout)
    return __shows_list_parse(json_data)

################################################################################
def shows_search(query):
    cache_key                    = 'shows-search-{0}'.format(query)
    cache_init_func              = functools.partial(__shows_search, query=query)
    cache_init_exception_handler = network.http_get_init_exception_handler
    cache_init_failure_handler   = network.http_get_init_failure_handler
    cache_update_func            = functools.partial(__shows_search, query=query, timeout=network.TIMEOUT_CONNECT)
    cache_data_expiration        = cache.DAY

    return cache.cache(cache_key, cache_init_func, cache_init_exception_handler, cache_init_failure_handler, cache_update_func, cache_data_expiration)

################################################################################
def shows_favorites(favorites):
    show_slugs = filter(None, favorites)
    show_infos = map(lambda show_slug : show(show_slug), show_slugs) or []
    return show_infos
