from flask import render_template
from example_app import app


@app.route('/')
def hello_word():
    context = {}
    return render_template('home.html', context=context)


@app.route('/home')
def home():
    return '<h2>Hello, home!</h2>'
