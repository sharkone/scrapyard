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
    page   = int(flask.request.args.get('page', '1'))
    limit  = int(flask.request.args.get('limit', '10'))
    result = scrapyard.movies_popular(page, limit)
    return flask.jsonify(result)

################################################################################
@app.route('/api/movies/trending')
def api_movies_trending():
    page   = int(flask.request.args.get('page', '1'))
    limit  = int(flask.request.args.get('limit', '10'))
    result = scrapyard.movies_trending(page, limit)
    return flask.jsonify(result)

################################################################################
@app.route('/api/movies/search')
def api_movies_search():
    query  =  flask.request.args.get('query', '')
    result = scrapyard.movies_search(query)
    return flask.jsonify(result)

################################################################################
@app.route('/api/movie/<trakt_slug>')
def api_movie(trakt_slug):
    result = scrapyard.movie(trakt_slug)
    return flask.jsonify(result)

################################################################################
# Shows
################################################################################
@app.route('/api/shows/popular')
def api_shows_popular():
    page   = int(flask.request.args.get('page', '1'))
    limit  = int(flask.request.args.get('limit', '10'))
    result = scrapyard.shows_popular(page, limit)
    return flask.jsonify(result)

################################################################################
@app.route('/api/shows/trending')
def api_shows_trending():
    page   = int(flask.request.args.get('page', '1'))
    limit  = int(flask.request.args.get('limit', '10'))
    result = scrapyard.shows_trending(page, limit)
    return flask.jsonify(result)

################################################################################
@app.route('/api/shows/search')
def api_shows_search():
    query  = flask.request.args.get('query', '')
    result = scrapyard.shows_search(query)
    return flask.jsonify(result)

################################################################################
@app.route('/api/show/<trakt_slug>')
def api_show(trakt_slug):
    result = scrapyard.show(trakt_slug)
    return flask.jsonify(result)

################################################################################
@app.route('/api/show/<trakt_slug>/season/<int:season_index>')
def api_show_season(trakt_slug, season_index):
    result = scrapyard.show_season(trakt_slug, season_index)
    return flask.jsonify(result)

################################################################################
@app.route('/api/show/<trakt_slug>/season/<int:season_index>/episode/<int:episode_index>')
def api_show_episode(trakt_slug, season_index, episode_index):
    result = scrapyard.show_episode(trakt_slug, season_index, episode_index)
    return flask.jsonify(result)

################################################################################
# Main
################################################################################
if __name__ == '__main__':
    app.run(debug=True, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), threaded=True)
