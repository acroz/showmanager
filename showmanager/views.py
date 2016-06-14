
from flask import (render_template, make_response, request, abort, redirect,
                   url_for, flash)
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime

from .app import app, db
from .models import Show, ShowDay, Class, Registrant, Entry
from . import forms
from .chits import chits as chitgen

@app.route('/')
def shows():
    shows = Show.query.join(ShowDay) \
                      .order_by(ShowDay.date) \
                      .all() 
    return render_template('shows.html', shows=shows)

@app.route('/show/<int:id>')
def show(id):
    query = Show.query.filter_by(id=id)
    try:
        show = query.one()
    except NoResultFound:
        abort(404)
    return render_template('show.html', show=show)

@app.route('/show/<int:id>/number', methods=['POST'])
def show_number(id):
    query = Show.query.filter_by(id=id)
    try:
        show = query.one()
    except NoResultFound:
        abort(404)
    show.assign_numbering()
    db.session.commit()
    flash('Numbering assigned', 'success')
    return redirect(url_for('show', id=show.id))

@app.route('/show/<int:id>/edit', methods=['GET', 'POST'])
def show_edit(id):
    query = Show.query.filter_by(id=id)
    try:
        show = query.one()
    except NoResultFound:
        abort(404)

    form = forms.ShowForm()

    # Handle submitted data
    if request.method == 'POST' and form.validate():

        # Update record
        show.name = form.name.data
        #show.start = form.start.data
        #show.end   = form.end.data
        show.registration_start = form.registration_start.data
        show.registration_end   = form.registration_end.data
        db.session.commit()

        flash('Show modified', 'success')

        return redirect(url_for('show', id=show.id))

    # Populate form
    form.name.data = show.name
    #form.start.data = show.start
    #form.end.data = show.end
    form.registration_start.data = show.registration_start
    form.registration_end.data = show.registration_end

    return render_template('show_edit.html', form=form, show=show)

@app.route('/show/<int:id>/register', methods=['GET', 'POST'])
def register(id):

    query = Show.query.filter_by(id=id)
    try:
        show = query.one()
    except NoResultFound:
        abort(404)

    if not show.registration_open:
        flash('Sorry, registration for this show is closed', 'danger')
        return redirect(url_for('show', id=show.id))

    # Build form
    EntryForm = forms.entry_form(show)
    form = EntryForm()
    
    # Handle submitted data
    if request.method == 'POST' and form.validate():

        # Create new registrant
        reg = Registrant(handler=form.handler.data,
                         dog=form.dog.data,
                         size=form.size.data,
                         grade=form.grade.data,
                         rescue=form.rescue.data,
                         collie=(not form.abc.data),
                         junior=form.junior.data)

        # Register class entries
        entries = []
        for class_id in form.classes.data:
            entries.append(Entry(registrant=reg, clss_id=int(id)))

        # Add registration to database session and update show
        db.session.add_all([reg] + entries)
        show.last_entry = datetime.utcnow()

        db.session.commit()

        flash('Thanks for registering', 'info')
        return redirect(url_for('show', id=show.id))

    return render_template('register.html', form=form, show=show)

@app.route('/class/<int:id>')
def clss(id):
    query = Class.query.filter_by(id=id)
    try:
        clss = query.one()
    except NoResultFound:
        abort(404)
    return render_template('class.html', clss=clss)

@app.route('/show/<int:id>/chits')
def show_chits(id):

    query = Show.query.filter_by(id=id)
    try:
        show = query.one()
    except NoResultFound:
        abort(404)

    if not show.numbering_up_to_date:
        flash('Assign chit numbering first', 'danger')
        return redirect(url_for('show', id=show.id))

    query_single = Entry.query.join(Class) \
                              .join(ShowDay) \
                              .filter(ShowDay.show == show) \
                              .join(Registrant) \
                              .order_by(Class.name) \
                              .order_by(Entry.number)

    query_league = Entry.query.join(Class) \
                              .filter(Class.league == show) \
                              .join(Registrant) \
                              .order_by(Class.name) \
                              .order_by(Entry.number)

    data = chitgen(query_league.all() + query_single.all(),
                   'tiled' in request.args)
    
    response = make_response(data)
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = 'filename="chits.pdf"'

    return response
