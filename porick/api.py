from flask import request, g, jsonify

from . import app
from .lib import (
    admin_endpoint, authenticated_endpoint, quote_belongs_to_user,
    has_made_too_many_reports)
from .models import QSTATUS, db, ReportedQuotes, Quote, VoteToUser


@app.route('/api/v1/quotes/<int:quote_id>/approve', methods=['POST'])
@admin_endpoint
def approve(quote_id):
    quote = Quote.query.get(quote_id)
    if not quote:
        return jsonify({'msg': 'Invalid quote ID.', 'status': 'error'})
    quote.status = QSTATUS['approved']
    db.session.commit()
    return jsonify({'msg': 'Quote approved.', 'status': 'success'})


@app.route('/api/v1/quotes/<int:quote_id>/disapprove', methods=['POST'])
@admin_endpoint
def disapprove(quote_id):
    delete_check = quote_belongs_to_user(quote_id)
    if delete_check['status'] == 'error':
        return jsonify(delete_check)
    else:
        quote = delete_check['quote']
    quote.status = QSTATUS['disapproved']
    msg = 'Quote disapproved.'
    db.session.commit()
    return jsonify({'msg': msg, 'status': 'success'})


@app.route('/api/v1/quotes/<int:quote_id>/delete', methods=['DELETE'])
@authenticated_endpoint
def delete(quote_id):
    delete_check = quote_belongs_to_user(quote_id)
    if delete_check['status'] == 'error':
        return jsonify(delete_check)
    else:
        quote = delete_check['quote']
    quote.status = QSTATUS['deleted']
    g.user.deleted_quotes.append(quote)
    msg = 'Quote deleted.'
    db.session.commit()
    return jsonify({'msg': msg, 'status': 'success'})


@app.route('/api/v1/quotes/<int:quote_id>/favourite', methods=['POST', 'DELETE'])
@authenticated_endpoint
def favourite(quote_id):
    quote = Quote.query.get(quote_id)
    if not quote:
        return jsonify({'msg': 'Invalid quote ID.', 'status': 'error'})
    if request.method == 'POST':
        g.user.favourites.append(quote)
        db.session.commit()
        return jsonify({'msg': 'Quote favourited.', 'status': 'success'})
    elif request.method == 'DELETE':
        if not quote in g.user.favourites:
            return jsonify({
                'msg': "Can't remove: This quote isn't in your favourites.",
                'status': 'error'})
        g.user.favourites.remove(quote)
        db.session.commit()
        return jsonify({'msg': 'Removed favourite.', 'status': 'success'})


@app.route('/api/v1/quotes/<int:quote_id>/report', methods=['POST'])
@authenticated_endpoint
def report(quote_id):
    quote = Quote.query.get(quote_id)
    if not quote:
        return jsonify({'msg': 'Invalid quote ID.', 'status': 'error'})
    if has_made_too_many_reports():
        return jsonify({'msg': 'You are reporting quotes too fast. Slow down!',
                        'status': 'error'})
    already_reported = db.session.query(ReportedQuotes).filter_by(
        user_id=g.user.id).filter_by(quote_id=quote.id).first()
    if already_reported:
        return jsonify({
            'msg': 'You already reported this quote in the past. Ignored.',
            'status': 'error'})
    if quote.status != QSTATUS['approved']:
        return jsonify({
            'msg': 'Quote is not approved, therefore cannot be reported.',
            'status': 'error'})
    g.user.reported_quotes.append(quote)
    quote.status = QSTATUS['reported']
    db.session.commit()
    return jsonify({'msg': 'Quote reported.', 'status': 'success'})


@app.route('/api/v1/quotes/<int:quote_id>/vote/<direction>', methods=['POST', 'DELETE'])
@authenticated_endpoint
def vote(quote_id, direction):
    if direction not in ['up', 'down']:
        return jsonify({'msg': 'Invalid vote direction.', 'status': 'error'})
    quote = Quote.query.get(quote_id)
    if request.method == 'POST':
        if not quote:
            return jsonify({'msg': 'Invalid quote ID.', 'status': 'error'})

        already_voted = ''
        for assoc in quote.voters:
            if assoc.user == g.user:
                already_voted = True
                # cancel the last vote:
                if assoc.direction == 'up':
                    quote.rating -= 1
                elif assoc.direction == 'down':
                    quote.rating += 1
                db.session.delete(assoc)

        assoc = VoteToUser(direction=direction)
        assoc.user = g.user
        quote.voters.append(assoc)

        if direction == 'up':
            quote.rating += 1
        elif direction == 'down':
            quote.rating -= 1

        if not already_voted:
            quote.votes += 1
        db.session.commit()
        return jsonify({'status': 'success', 'msg': 'Vote cast!'})
    elif request.method == 'DELETE':
        for assoc in quote.voters:
            if assoc.user == g.user:
                db.session.delete(assoc)
        if direction == 'up':
            quote.rating -= 1
        elif direction == 'down':
            quote.rating += 1

        quote.votes -= 1
        db.session.commit()
        return jsonify({'status': 'success', 'msg': 'Vote annulled!'})
