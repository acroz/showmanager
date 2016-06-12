
from flask import render_template, make_response, request, abort, redirect, url_for, flash
from .app import app, db
from .models import Show, Class, Registrant, Entry
from .forms import entry_form
from .chits import chits as chitgen

@app.route('/')
def shows():
    shows = Show.query.order_by(Show.datestart).all() 
    return render_template('shows.html', shows=shows)

@app.route('/show/<int:id>')
def show(id):
    query = Show.query.filter_by(id=id)
    try:
        show = query.one()
    except NoResultFound:
        abort(404)
    return render_template('show.html', show=show)

@app.route('/class/<int:id>')
def clss(id):
    query = Class.query.filter_by(id=id)
    try:
        clss = query.one()
    except NoResultFound:
        abort(404)
    return render_template('class.html', clss=clss)

@app.route('/register/<int:show_id>', methods=['GET', 'POST'])
def register(show_id):

    query = Show.query.filter_by(id=show_id)
    try:
        show = query.one()
    except NoResultFound:
        abort(404)

    # Build form
    EntryForm = entry_form(show)
    form = EntryForm(request.form)
    
    # Handle submitted data
    if request.method == 'POST' and form.validate():
        reg = Registrant(handler=form.handler.data, dog=form.dog.data)
        entries = []
        for clss in show.classes:
            if getattr(form, clss.id_string):
                entries.append(Entry(registrant=reg, clss=clss))
        db.session.add_all([reg] + entries)
        db.session.commit()
        flash('Thanks for registering')
        return redirect(url_for('show', id=show.id))

    return render_template('register.html', form=form, show=show)

@app.route('/chits')
def chits():
    
    data = chitgen(Entry.query.all(), 'tiled' in request.args)
    
    response = make_response(data)
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = 'filename="chits.pdf"'

    return response
