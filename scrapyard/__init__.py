import cache
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

    magnets     = []
    info_hashes = set()

    for provider_magnet_list in provider_magnet_lists:
        for magnet in provider_magnet_list:
            if magnet.info_hash not in info_hashes:
                magnets.append(magnet)
                info_hashes.add(magnet.info_hash)

    scraper.scrape_magnets(magnets, timeout=1)
    magnets = filter(lambda magnet: magnet.seeds > 0, magnets)
    magnets = sorted(magnets, key=lambda magnet: magnet.seeds, reverse=True)
    magnets = [{'link': magnet.link, 'title': magnet.title, 'seeds': magnet.seeds, 'peers': magnet.peers } for magnet in magnets]

    return magnets

################################################################################
# Movies
################################################################################
def movies_popular(page, limit):
    return trakt.movies_popular(page, limit)

################################################################################
def movies_trending(page, limit):
    return trakt.movies_trending(page, limit)

################################################################################
def movies_search(query):
    return trakt.movies_search(query)

################################################################################
def movie(trakt_slug):
    movie_info = trakt.movie(trakt_slug, people_needed=True)
    if movie_info:
        movie_info['magnets'] = cache.cache(__movie_magnets, expiration=cache.HOUR, cache_key=trakt_slug)([ kickass, yts ], movie_info) or []
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
    episode_info = trakt.show_episode(trakt_slug, season_index, episode_index)
    if episode_info:
        show_info = trakt.show(trakt_slug)
        if show_info:
            episode_info['magnets'] = cache.cache(__show_episode_magnets, expiration=cache.HOUR, cache_key='{0}-{1}-{2}'.format(trakt_slug, season_index, episode_index))([ eztv, kickass ], show_info, episode_info) or []
    return episode_info

################################################################################
def __show_episode_magnets(providers, show_info, episode_info):
    return __populate_magnets(providers, functools.partial(lambda module, show_info, episode_info: module.episode(show_info, episode_info), show_info=show_info, episode_info=episode_info))

# ################################################################################
def shows_popular(page, limit):
    return { 'shows': trakt.shows_popular(page, limit) }

################################################################################
def shows_trending(page, limit):
    return { 'shows': trakt.shows_trending(page, limit) }

################################################################################
def shows_search(query):
    return { 'shows': trakt.shows_search(query) }
