#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default

import sys
import datetime
from collections import OrderedDict
import pandoc

from flask import Flask
from flask import render_template, redirect, url_for
from flask.ext.babel import Babel
from flask_flatpages import FlatPages
from flask_frozen import Freezer

# TODO:
# * Get babel locale from request path

# Create the Flask app
app = Flask(__name__)

# Load settings
app.config.from_pyfile('settings/common.py')
app.config.from_pyfile('settings/local_settings.py', silent=True)

if len(sys.argv) > 2:
    extra_conf = sys.argv[2]
    app.config.from_pyfile('settings/{}_settings.py'.format(extra_conf), silent=True)

# Add the babel extension
babel = Babel(app)

# Add the FlatPages extension
pages = FlatPages(app)


# Add the Frozen extension
freezer = Freezer(app)

#
# Utils
#

# Frozen url generators

@freezer.register_generator
def default_locale_urls():
    ''' Genarates the urls for default locale without prefix. '''
    for page in pages:
        if not 'main' in page.path:
            yield '/{}/'.format(remove_l10n_prefix(page.path))


@freezer.register_generator
def page_urls():
    ''' Genarates the urls with locale prefix. '''
    for page in pages:
        if not 'main' in page.path:
            yield '/{}/'.format(page.path)

# l10n helpers

def has_l10n_prefix(path):
    ''' Verifies if the path have a localization prefix. '''
    return reduce(lambda x, y: x or y, [path.startswith(l)
                  for l in app.config.get('AVAILABLE_LOCALES', [])])


def add_l10n_prefix(path, locale=app.config.get('DEFAULT_LOCALE')):
    '''' Add localization prefix if necessary. '''
    return path if has_l10n_prefix(path) else '{}/{}'.format(locale, path)


def remove_l10n_prefix(path, locale=app.config.get('DEFAULT_LOCALE')):
    ''' Remove specific localization prefix. '''
    return path if not path.startswith(locale) else path[(len(locale) + 1):]

# Make remove_l10n_prefix accessible to Jinja
app.jinja_env.globals.update(remove_l10n_prefix=remove_l10n_prefix)

# Structure helpers

def render_markdown(text):
    ''' Render Markdown text to HTML. '''
    doc = pandoc.Document()
    doc.markdown = text.encode('utf8')
    return unicode(doc.html, 'utf8')

app.config['FLATPAGES_HTML_RENDERER'] = render_markdown

#
# Routes
#

@app.route('/')
def root():
    ''' Main page '''
    # Get the page
    path = 'main'
    page = pages.get_or_404(add_l10n_prefix(path))

    return render_template('root.html', page=page, pages=pages)

@app.route('/<path:path>/')
def page(path):
    ''' All pages from markdown files '''

    # Get the page
    page = pages.get_or_404(add_l10n_prefix(path))

    # Get custom template
    template = page.meta.get('template', 'page.html')

    # Verify if need redirect
    redirect_ = page.meta.get('redirect', None)
    if redirect_:
        return redirect(url_for('page', path=redirect_))

    today = datetime.datetime.now().strftime("%B %dth %Y")

    # Render the page
    return render_template(template, page=page, today=today, pages=pages)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        freezer.freeze()
    else:
        app.run(port=8000)
