import exceptions
import network
import requests
import scraper

EZTV_URL = 'https://www.popcorntime.ws/api/eztv/'

################################################################################
def episode(show_info, episode_info):
    magnet_infos = []

    if show_info['imdb_id']:
        try:
            json_data = network.json_get(EZTV_URL + '/show/' + show_info['imdb_id'])
            if json_data and json_data['episodes']:
                for json_item in json_data['episodes']:
                    if json_item['season'] == episode_info['season_index'] and json_item['episode'] == episode_info['episode_index']:
                        for value in json_item['torrents'].values():
                            magnet_infos.append(scraper.Magnet(value['url'], None, value['seeds'], value['peers'], 0))
                        break
        except requests.exceptions.HTTPError as exception:
            if exception.response.status_code in (404, 503):
                pass
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass
        except exceptions.JSONError:
            pass

    return magnet_infos
