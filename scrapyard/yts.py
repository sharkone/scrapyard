import cache
import network
import scraper

YTS_URL = 'http://yts.re'

################################################################################
def movie(movie_info):
    magnet_infos = []

    json_data = network.json_get_cached_optional(YTS_URL + '/api/listimdb.json', expiration=cache.HOUR, params={ 'imdb_id': movie_info['imdb_id'] })
    if 'MovieList' in json_data:
        for json_item in json_data['MovieList']:
            title = '{0} ({1}) {2} - YIFY'.format(json_item['MovieTitleClean'], json_item['MovieYear'], json_item['Quality'])
            magnet_infos.append(scraper.Magnet(json_item['TorrentMagnetUrl'], title, int(json_item['TorrentSeeds']), int(json_item['TorrentPeers'])))

    return magnet_infos
