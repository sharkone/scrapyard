import cache
import datetime
import eztv
import functools
import kickass
import scraper
import trakt
import utils
import yts

################################################################################
# Common
################################################################################
def __populate_magnets(providers, func):
    provider_magnet_lists = map(func, providers)

    magnets = {}

    for provider_magnet_list in provider_magnet_lists:
        for magnet in provider_magnet_list:
            if (magnet.info_hash not in magnets) or (magnet.size > magnets[magnet.info_hash].size):
                magnets[magnet.info_hash] = magnet

    magnets = magnets.values()
    scraper.scrape_magnets(magnets, timeout=1)
    magnets = filter(lambda magnet: magnet.seeds > 0, magnets)
    magnets = sorted(magnets, key=lambda magnet: magnet.seeds, reverse=True)
    magnets = [{'link': magnet.link, 'title': magnet.title, 'seeds': magnet.seeds, 'peers': magnet.peers, 'size': magnet.size } for magnet in magnets]

    return magnets

################################################################################
# Movies
################################################################################
def movies_popular(page):
    return trakt.movies_popular(page)

################################################################################
def movies_trending(page):
    return trakt.movies_trending(page)

################################################################################
def movies_watchlist(watchlist):
    return trakt.movies_watchlist(watchlist)

################################################################################
def movies_search(query):
    return trakt.movies_search(query)

################################################################################
def movie(trakt_slug):
    movie_info = trakt.movie(trakt_slug, people_needed=True)

    cache_key             = 'movie-{0}-magnets'.format(trakt_slug)
    #cache_update_func     = functools.partial(__movie_magnets, providers=[ kickass, yts ], movie_info=movie_info)
    cache_update_func     = functools.partial(__movie_magnets, providers=[ kickass ], movie_info=movie_info)
    cache_data_expiration = cache.HOUR * 2
    movie_info['magnets'] = cache.cache_optional(cache_key, cache_update_func, cache_data_expiration) or []

    return movie_info

################################################################################
def __movie_magnets(providers, movie_info):
    return __populate_magnets(providers, functools.partial(lambda module, movie_info: module.movie(movie_info), movie_info=movie_info))

################################################################################
# Shows
################################################################################
def show(trakt_slug):
    return trakt.show(trakt_slug, seasons_needed=True)

################################################################################
def show_season(trakt_slug, season_index):
    return trakt.show_season(trakt_slug, season_index)

################################################################################
def show_episode(trakt_slug, season_index, episode_index):
    show_info    = trakt.show(trakt_slug)
    episode_info = trakt.show_episode(trakt_slug, season_index, episode_index)

    cache_key               = 'show-{0}-{1}-{2}-magnets'.format(trakt_slug, season_index, episode_index)
    # cache_update_func       = functools.partial(__show_episode_magnets, providers=[ eztv, kickass ], show_info=show_info, episode_info=episode_info)
    cache_update_func       = functools.partial(__show_episode_magnets, providers=[ eztv, kickass ], show_info=show_info, episode_info=episode_info)
    cache_data_expiration   = cache.HOUR * 2
    episode_info['magnets'] = cache.cache_optional(cache_key, cache_update_func, cache_data_expiration) or []

    return episode_info

################################################################################
def __show_episode_magnets(providers, show_info, episode_info):
    return __populate_magnets(providers, functools.partial(lambda module, show_info, episode_info: module.episode(show_info, episode_info), show_info=show_info, episode_info=episode_info))

# ################################################################################
def shows_popular(page):
    return trakt.shows_popular(page)

################################################################################
def shows_trending(page):
    return trakt.shows_trending(page)

################################################################################
def shows_favorites(favorites):
    return trakt.shows_favorites(favorites)

################################################################################
def shows_search(query):
    return trakt.shows_search(query)
