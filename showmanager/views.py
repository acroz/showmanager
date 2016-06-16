
from flask import (render_template, make_response, request, abort, redirect,
                   url_for, flash)
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime

from .app import app, db
from .models import League, Round, Class, Entry
from . import forms
from .chits import chits as chitgen

@app.route('/')
def leagues():
    leagues = League.query.join(Round) \
                          .order_by(Round.date) \
                          .all() 
    return render_template('leagues.html', leagues=leagues)

@app.route('/league/<int:id>')
def league(id):
    query = League.query.filter_by(id=id)
    try:
        league = query.one()
    except NoResultFound:
        abort(404)
    return render_template('league.html', league=league)

@app.route('/league/<int:id>/number', methods=['POST'])
def league_number(id):
    query = League.query.filter_by(id=id)
    try:
        league = query.one()
    except NoResultFound:
        abort(404)
    league.assign_numbering()
    db.session.commit()
    flash('Numbering assigned', 'success')

    try:
        return redirect(request.form['redirect'])
    except KeyError:
        return redirect(url_for('league', id=league.id))

@app.route('/league/<int:id>/edit', methods=['GET', 'POST'])
def league_edit(id):
    query = League.query.filter_by(id=id)
    try:
        league = query.one()
    except NoResultFound:
        abort(404)

    form = forms.LeagueForm()

    # Handle submitted data
    if request.method == 'POST' and form.validate():

        # Update record
        league.name = form.name.data
        #league.start = form.start.data
        #league.end   = form.end.data
        league.registration_start = form.registration_start.data
        league.registration_end   = form.registration_end.data
        db.session.commit()

        flash('Show modified', 'success')

        return redirect(url_for('league', id=league.id))

    # Populate form
    form.name.data = league.name
    #form.start.data = league.start
    #form.end.data = league.end
    form.registration_start.data = league.registration_start
    form.registration_end.data = league.registration_end

    return render_template('league_edit.html', form=form, league=league)

@app.route('/league/<int:id>/register', methods=['GET', 'POST'])
def register(id):

    query = League.query.filter_by(id=id)
    try:
        league = query.one()
    except NoResultFound:
        abort(404)

    if not league.registration_open:
        flash('Sorry, registration for {} is closed'.format(league.name), 'danger')
        return redirect(url_for('league', id=league.id))

    # Build form
    form = forms.EntryForm()
    
    # Handle submitted data
    if request.method == 'POST' and form.validate():

        # Create new registrant
        entry = Entry(handler=form.handler.data,
                      dog=form.dog.data,
                      size=form.size.data,
                      grade=form.grade.data,
                      rescue=form.rescue.data,
                      collie=(not form.abc.data),
                      junior=form.junior.data)

        # Add registration to database session and update show
        db.session.add(entry)
        league.last_entry = datetime.utcnow()

        db.session.commit()

        flash('Thanks for registering', 'info')
        return redirect(url_for('league', id=league.id))

    return render_template('register.html', form=form, league=league)

@app.route('/round/<int:id>')
def round(id):
    query = Round.query.filter_by(id=id)
    try:
        round = query.one()
    except NoResultFound:
        abort(404)
    return render_template('round.html', round=round)

@app.route('/round/<int:id>/chits')
def round_chits(id):

    query = Round.query.filter_by(id=id)
    try:
        round = query.one()
    except NoResultFound:
        abort(404)

    league = round.league

    if not league.numbering_up_to_date:
        flash('Assign chit numbering first', 'danger')
        return redirect(url_for('league', id=league.id))
    
    class_names = ['{} Round {}'.format(c.name, round.id) for c in league.classes]

    data = chitgen(class_names, league.entries, 'tiled' in request.args)
    
    response = make_response(data)
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = 'filename="chits.pdf"'

    return response
