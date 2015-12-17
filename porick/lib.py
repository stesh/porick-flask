from flask import request

def current_page(default=1):
    try:
        return int(request.args.get('page', default))
    except ValueError:
        return default
