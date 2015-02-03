import cache
import network
import requests
import scraper

EZTV_URL = 'http://eztvapi.re'

################################################################################
def episode(show_info, episode_info):
    magnet_infos = []

    if show_info['imdb_id']:
        try:
            json_data = network.json_get_cached(EZTV_URL + '/show/' + show_info['imdb_id'], expiration=cache.HOUR)
            if json_data and json_data['episodes']:
                for json_item in json_data['episodes']:
                    if json_item['season'] == episode_info['season_index'] and json_item['episode'] == episode_info['episode_index']:
                        for value in json_item['torrents'].values():
                            magnet_infos.append(scraper.Magnet(value['url'], None, value['seeds'], value['peers']))
                        break
        except requests.exceptions.HTTPError as exception:
            if exception.response.status_code != 404:
                raise exception
        except requests.exceptions.Timeout:
            pass

    return magnet_infos
