import flask
import os
import scrapyard

################################################################################
app = flask.Flask(__name__)

################################################################################
# Routes
################################################################################
@app.route('/')
def index():
    return ''

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
# Main
################################################################################
if __name__ == '__main__':
    app.run(debug=True, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
