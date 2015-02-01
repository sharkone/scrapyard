import cache
import network
import scraper

EZTV_URL = 'http://eztvapi.re'

################################################################################
def episode(show_info, episode_info):
    magnet_infos = []

    if show_info['imdb_id']:
        json_data = network.json_get_cached_optional(EZTV_URL + '/show/' + show_info['imdb_id'], expiration=cache.HOUR)
        if json_data and json_data['episodes']:
            for json_item in json_data['episodes']:
                if json_item['season'] == episode_info['season_index'] and json_item['episode'] == episode_info['episode_index']:
                    for key, value in json_item['torrents'].iteritems():
                        magnet_infos.append(scraper.Magnet(value['url'], None, value['seeds'],value['peers']))
                    break

    return magnet_infos
