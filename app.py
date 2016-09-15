from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from example_app import app as example_app

app = DispatcherMiddleware(example_app, {})

if __name__ == '__main__':
    run_simple('localhost', 5000, app,
               use_reloader=True,
               use_debugger=True,
               use_evalex=True)
