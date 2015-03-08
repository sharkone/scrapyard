import flask
import os
import scrapyard

################################################################################
# App
################################################################################
class ScrapyardJSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        try:
            return flask.json.JSONEncoder.default(self, obj)
        except TypeError:
            pass

        try:
            return flask.json.JSONEncoder.default(self, list(iter(obj)))
        except TypeError:
            pass

        return flask.json.JSONEncoder.default(self, obj.__dict__)

################################################################################
app              = flask.Flask(__name__)
app.json_encoder = ScrapyardJSONEncoder

################################################################################
@app.route('/')
def index():
    return ''

################################################################################
# Movies
################################################################################
@app.route('/api/movies/popular')
def api_movies_popular():
    try:
        page = flask.request.args.get('page', '1', type=int)
        return flask.jsonify({ 'movies': scrapyard.movies_popular(page) })
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/movies/trending')
def api_movies_trending():
    try:
        page = flask.request.args.get('page', '1', type=int)
        return flask.jsonify({ 'movies': scrapyard.movies_trending(page) })
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/movies/watchlist')
def api_movies_watchlist():
    trakt_slugs = flask.request.args.getlist('id')
    return flask.jsonify({ 'movies': scrapyard.movies_watchlist(trakt_slugs) })

################################################################################
@app.route('/api/movies/search')
def api_movies_search():
    try:
        query = flask.request.args.get('query', '')
        return flask.jsonify({ 'movies': scrapyard.movies_search(query) })
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/movie/<trakt_slug>')
def api_movie(trakt_slug):
    try:
        return flask.jsonify(scrapyard.movie(trakt_slug))
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
# Shows
################################################################################
@app.route('/api/shows/popular')
def api_shows_popular():
    try:
        page = flask.request.args.get('page', '1', type=int)
        return flask.jsonify({ 'shows': scrapyard.shows_popular(page) })
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/shows/trending')
def api_shows_trending():
    try:
        page = flask.request.args.get('page', '1', type=int)
        return flask.jsonify({ 'shows': scrapyard.shows_trending(page) })
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/shows/favorites')
def api_shows_favorites():
    trakt_slugs = flask.request.args.getlist('id')
    return flask.jsonify({ 'shows': scrapyard.shows_favorites(trakt_slugs) })

################################################################################
@app.route('/api/shows/search')
def api_shows_search():
    try:
        query = flask.request.args.get('query', '')
        return flask.jsonify({ 'shows': scrapyard.shows_search(query) })
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/show/<trakt_slug>')
def api_show(trakt_slug):
    try:
        return flask.jsonify(scrapyard.show(trakt_slug))
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/show/<trakt_slug>/season/<int:season_index>')
def api_show_season(trakt_slug, season_index):
    try:
        return flask.jsonify({ 'episodes': scrapyard.show_season(trakt_slug, season_index) })
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
@app.route('/api/show/<trakt_slug>/season/<int:season_index>/episode/<int:episode_index>')
def api_show_episode(trakt_slug, season_index, episode_index):
    try:
        return flask.jsonify(scrapyard.show_episode(trakt_slug, season_index, episode_index))
    except scrapyard.exceptions.HTTPError as exception:
        flask.abort(exception.status_code)

################################################################################
# Main
################################################################################
if __name__ == '__main__':
    app.run(debug=True, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), threaded=True)
