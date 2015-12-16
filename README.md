# porick-flask
Porting [Porick](github.com/kopf/porick) to Flask

## Getting started
    $ mkvirtualenv porick-flask
    $ git clone https://github.com/stesh/porick-flask.git
    $ cd porick-flask
    $ pip install -r requirements.txt

## Running locally

* Create a file in `settings/` in which to store your settings, e.g. `settings/dev.py`
* Create `settings/__init__.py` with the contents: `from .dev import *`
(this allows you to have multiple sets of settings you can switch between easily)
* Fill your `dev.py` file with the settings detailed in `settings.example`
* `python runserver.py`

## Database setup

```
>>> from porick.model.meta import Base, engine
>>> Base.metadata.create_all(engine)
>>>
```
