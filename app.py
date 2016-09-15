#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_word():
    return '<h1>Hello, world!</h1>'


@app.route('/home')
def home():
    return '<h2>Hello, home!</h2>'
