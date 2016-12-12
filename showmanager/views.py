from flask import (render_template, make_response, request, abort, redirect,
                   url_for, flash)
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta

from .app import app, db
from .models import League, Round, Class, Course, Entry
from .util import HTMLTable, PointsTable
from . import forms
from .chit import chits as chitgen


@app.route('/')
def leagues():
    leagues = League.query.join(Round) \
                          .order_by(Round.date) \
                          .all()
    return render_template('leagues.html', leagues=leagues)


@app.route('/league/<int:id>')
def league(id):
    print(id)
    league = League.query.filter_by(id=id).first_or_404()
    return render_template('league.html', league=league)


@app.route('/league/<int:id>/number', methods=['POST'])
def league_number(id):
    league = League.query.filter_by(id=id).first_or_404()
    league.assign_numbering()
    db.session.commit()
    flash('Numbering assigned', 'success')

    try:
        return redirect(request.form['redirect'])
    except KeyError:
        return redirect(url_for('league', id=league.id))


@app.route('/league/<int:id>/edit', methods=['GET', 'POST'])
def league_edit(id):
    league = League.query.filter_by(id=id).first_or_404()

    LeagueForm = forms.league_form(league)
    form = LeagueForm()

    # Handle submitted data
    if request.method == 'POST' and form.validate():

        # Update record
        league.name = form.name.data
        league.registration_start = form.registration_start.data
        league.registration_end = form.registration_end.data
        league.scoring_rounds = form.scoring_rounds.data

        # Delete extra rounds
        extra = len(league.rounds) - form.num_rounds.data
        if extra > 0:
            flash('{} rounds deleted'.format(extra), 'info')
            for round in league.rounds[-extra:]:
                db.session.delete(round)

        # Add new rounds
        new = form.num_rounds.data - len(league.rounds)
        if new > 0:
            flash('{} new rounds added'.format(new), 'info')
            day = timedelta(days=1)
            first = league.rounds[-1].date + day
            for i in range(new):
                round = Round(league=league, date=(first + i * day))
                db.session.add(round)

        db.session.commit()

        flash('League updated', 'success')

        return redirect(url_for('league_edit', id=league.id))

    # Populate form
    form.name.data = league.name
    form.num_rounds.data = len(league.rounds)
    form.scoring_rounds.data = league.scoring_rounds
    for i, round in enumerate(league.rounds):
        form['round_{}'.format(i+1)].data = round.date
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
        flash('Sorry, registration for {} is closed'.format(league.name),
              'danger')
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


@app.route('/league/<int:id>/overall')
def league_overall(id):
    league = League.query.filter_by(id=id).first_or_404()

    table = PointsTable(league.entries,
                        [round.shortname for round in league.rounds],
                        league.scoring_rounds)

    for round in league.rounds:
        for course in round.courses:
            for score in course.scores:
                table.accumulate(score.entry, round.shortname, score.points)

    return render_template('league_overall.html', league=league, table=table)


@app.route('/round/<int:id>')
def round(id):
    round = Round.query.filter_by(id=id).first_or_404()
    league = round.league

    table = PointsTable(league.entries,
                        [clss.name for clss in league.classes])

    for course in round.courses:
        for score in course.scores:
            table.accumulate(score.entry, course.clss.name, score.points)

    return render_template('round.html', round=round, table=table)


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
        return redirect(url_for('round', id=round.id))

    class_names = ['{} Round {}'.format(c.name, round.id)
                   for c in league.classes]

    data = chitgen(class_names, league.entries, 'tiled' in request.args)

    response = make_response(data)
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = 'filename="chits.pdf"'

    return response


@app.route('/class/<int:id>')
def clss(id):

    clss = Class.query.filter_by(id=id).first_or_404()
    league = clss.league

    table = PointsTable(league.entries,
                        [round.shortname for round in league.rounds],
                        league.scoring_rounds)

    for course in clss.courses:
        for score in course.scores:
            table.accumulate(score.entry, course.round.shortname, score.points)

    return render_template('class.html', clss=clss, table=table)


@app.route('/course/<int:id>')
def course(id):

    course = Course.query.filter_by(id=id).first_or_404()

    headers = ['Rank', 'Dog No.', 'Handler', 'Dog', 'HRAJ1', 'Time',
               'Time Faults', 'Jumping Faults', 'Total Faults', 'Points']

    def ff(v): return '{:.3f}'.format(v)

    data = []
    for i, score in enumerate(course.scores):
        entry = score.entry
        row = [i+1, entry.number,  entry.handler, entry.dog, entry.hraj1]

        if score.eliminated:
            row += ['E'] * 4
        elif score.noshow:
            row += ['NS'] * 4
        else:
            row += [ff(score.time), ff(score.time_faults), score.faults,
                    ff(score.total_faults)]
        row.append(score.points)
        data.append(row)

    table = HTMLTable(headers, data)

    return render_template('course.html', course=course, table=table)
