import flask
import os
import redis
import urlparse

################################################################################
app = flask.Flask(__name__)

redis_url        = urlparse.urlparse(os.environ.get('REDISCLOUD_URL', 'redis://{0}:{1}'.format(os.getenv('IP', '0.0.0.0'), 6379)))
redis_connection = redis.StrictRedis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

################################################################################
# Routes
################################################################################
@app.route('/')
def index():
    return 'Hello world!'

################################################################################
@app.route('/set')
def set():
    key   = flask.request.args.get('key', 'test_key')
    value = flask.request.args.get('value', 'test_value')
    redis_connection.set(key, value)
    return 'Key {0} successfully set to {1}'.format(key, value)

################################################################################
@app.route('/get')
def get():
    key   = flask.request.args.get('key', 'test_key')
    value = redis_connection.get(key)
    if value:
        return 'Key {0} = {1}'.format(key, value)
    else:
        flask.abort(404)

################################################################################
@app.route('/flushall')
def flushall():
    redis_connection.flushall()
    return 'Database successfully flushed'

################################################################################
# Main
################################################################################
if __name__ == '__main__':
    app.run(debug=True, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
