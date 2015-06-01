import exceptions
import network
import requests
import scraper
import urllib

KICKASS_URL = 'http://kickass.to'

################################################################################
def movie(movie_info):
    return __search('category:{0} imdb:{1}'.format('movies', movie_info['imdb_id'][2:]))

################################################################################
def episode(show_info, episode_info):
    clean_title = show_info['title'].replace('?', '')
    advanced_search_results = __search('category:{0} {1} season:{2} episode:{3}'.format('tv', clean_title, episode_info['season_index'], episode_info['episode_index']))
    naive_search_results    = __search('category:{0} {1} S{2:02}E{3:02}'.format('tv', clean_title, episode_info['season_index'], episode_info['episode_index']))
    return advanced_search_results + naive_search_results

################################################################################
def __search(query):
    magnet_infos = []

    try:
        rss_data = network.rss_get(KICKASS_URL + '/usearch/{0}/'.format(urllib.quote(query)), params={ 'field': 'seeders', 'sorder': 'desc', 'rss': '1' })
        if rss_data:
            for rss_item in rss_data.entries:
                magnet_infos.append(scraper.Magnet(rss_item.torrent_magneturi, rss_item.title, int(rss_item.torrent_seeds), int(rss_item.torrent_peers), int(rss_item.torrent_contentlength)))
    except requests.exceptions.HTTPError as exception:
        if exception.response.status_code in (404, 503):
            pass
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pass

    return magnet_infos
