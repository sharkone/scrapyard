import cache
import network
import requests
import scraper
import urllib

KICKASS_URL = 'http://kickass.so'

################################################################################
def movie(movie_info):
    return __search('category:{0} imdb:{1}'.format('movies', movie_info['imdb_id'][2:]))

################################################################################
def episode(show_info, episode_info):
    clean_title = show_info['title'].replace('?', '')
    return __search('category:{0} {1} season:{2} episode:{3}'.format('tv', clean_title, episode_info['season_index'], episode_info['episode_index']))

################################################################################
def __search(query):
    magnet_infos = []

    try:
        rss_data = network.rss_get_cached(KICKASS_URL + '/usearch/{0}'.format(urllib.quote(query)), expiration=cache.HOUR, params={ 'field': 'seeders', 'sorder': 'desc', 'rss': '1' })
        if rss_data:
            for rss_item in rss_data.entries:
                magnet_infos.append(scraper.Magnet(rss_item.torrent_magneturi, rss_item.title, int(rss_item.torrent_seeds), int(rss_item.torrent_peers)))
    except requests.exceptions.HTTPError as exception:
        if exception.response.status_code != 404:
            raise exception
    except requests.exceptions.Timeout as exception:
        pass

    return magnet_infos
