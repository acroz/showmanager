from .app import db
from datetime import datetime


class League(db.Model):

    __tablename__ = 'leagues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    registration_start = db.Column(db.DateTime)
    registration_end = db.Column(db.DateTime)

    classes = db.relationship('Class', back_populates='league')
    rounds = db.relationship('Round', order_by='Round.date',
                             back_populates='league')
    entries = db.relationship('Entry', order_by='Entry.handler',
                              back_populates='league')

    @property
    def registration_open(self):
        if self.registration_start is None or self.registration_end is None:
            return False
        now = datetime.utcnow()
        return self.registration_start <= now <= self.registration_end


class Round(db.Model):

    __tablename__ = 'rounds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'),
                          nullable=False)
    league = db.relationship('League', back_populates='rounds')

    @property
    def number(self):
        sibling_ids = [round.id for round in self.league.rounds]
        return sibling_ids.index(self.id) + 1


class Class(db.Model):

    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'),
                          nullable=False)
    league = db.relationship('League', back_populates='classes')


class Entry(db.Model):

    __tablename__ = 'entries'

    id = db.Column(db.Integer, primary_key=True)
    handler = db.Column(db.String)
    dog = db.Column(db.String)
    size = db.Column(db.Enum('S', 'M', 'L'))
    grade = db.Column(db.Integer)
    rescue = db.Column(db.Boolean)
    collie = db.Column(db.Boolean)
    junior = db.Column(db.Boolean)

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'),
                          nullable=False)
    league = db.relationship('League', back_populates='entries')

    scores = db.relationship('Score', back_populates='entry')

    @property
    def hraj1(self):
        hraj1 = str(self.size)
        if self.rescue:
            hraj1 += '/R'
        if not self.collie:
            hraj1 += '/A'
        if self.junior:
            hraj1 += '/J'
        if self.grade == 1:
            hraj1 += '/1'
        return hraj1


class Course(db.Model):

    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))

    round = db.relationship('Round')
    class_ = db.relationship('Class')

    time = db.Column(db.Float)

    scores = db.relationship('Score', back_populates='course')

    def update_points(self):

        # Group scores by eliminated/clear round/with faults
        clear_rounds = []
        with_faults = []
        eliminated = []
        for score in self.scores:
            if score.eliminated:
                eliminated.append(score)
            elif score.clear_round:
                clear_rounds.append(score)
            else:
                with_faults.append(score)

        # Sort clear rounds by time (smallest first)
        clear_rounds = sorted(clear_rounds, key=lambda s: s.time)
        # Sort rounds with faults by total faults (smallest first)
        with_faults = sorted(clear_rounds, key=lambda s: s.total_faults)

        # Get total entrants in league
        n_entrants = Entry.query.filter_by(league=self.round.league) \
                                .count()

        # Assign points
        # Non-eliminated rounds are assigned points in order, with the best
        # score getting a number of points equal to the number of participants
        # in the competition
        for i, score in enumerate(clear_rounds + with_faults):
            score.points = n_entrants - i
        # Eliminated rounds get 1 point each
        for score in eliminated:
            score.points = 1

        db.session.commit()


class Score(db.Model):

    __tablename__ = 'scores'

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'),
                          primary_key=True)
    course = db.relationship('Course', back_populates='scores')

    entry_id = db.Column(db.Integer, db.ForeignKey('entries.id'),
                         primary_key=True)
    entry = db.relationship('Entry', back_populates='scores')

    time = db.Column(db.Float)
    faults = db.Column(db.Integer)
    eliminated = db.Column(db.Boolean, default=False)
    points = db.Column(db.Integer)

    @property
    def time_faults(self):
        if self.eliminated:
            return None
        time_over = self.time - self.course.time
        return time_over if time_over > 0. else 0.

    @property
    def total_faults(self):
        if self.eliminated:
            return None
        return self.faults + self.time_faults

    @property
    def clear_round(self):
        return self.total_faults == 0


def initialise():
    """Create the schema"""
    db.create_all()


def populate():
    """
    Temporary for development: Populate some data
    """
    from datetime import date, datetime

    league = League(name='Winter League 2016-17',
                    registration_start=datetime(2016, 6, 1),
                    registration_end=datetime(2016, 8, 31))
    db.session.add(league)

    league_old = League(name='Winter League Old',
                        registration_start=datetime(2015, 6, 1),
                        registration_end=datetime(2015, 8, 31))
    db.session.add(league_old)

    r1 = Round(name='Round 1', date=date(2016, 9, 10), league=league)
    r2 = Round(name='Round 2', date=date(2016, 9, 17), league=league)
    r3 = Round(name='Round 3', date=date(2016, 9, 24), league=league)
    r4 = Round(name='Round 4', date=date(2016, 10, 1), league=league)
    r5 = Round(name='Round 5', date=date(2016, 10, 8), league=league)
    r6 = Round(name='Round 6', date=date(2016, 10, 15), league=league)
    db.session.add_all([r1, r2, r3, r4, r5, r6])

    db.session.add(Round(name='Round 1', date=date(2015, 12, 31),
                         league=league_old))

    c1 = Class(name='Agility', league=league)
    c2 = Class(name='Jumping', league=league)
    db.session.add_all([c1, c2])

    longname = 'Really ' + 'really ' * 30 + ' long name'
    entries = [Entry(handler='Some guy with a super duper long name',
                     dog=longname,
                     size='S', grade=1, rescue=True, collie=False, junior=True,
                     league=league),
               Entry(handler='Andrew Crozier', dog='Caffrey',
                     size='M', grade=2, rescue=False, collie=True, junior=True,
                     league=league),
               Entry(handler='Lynda Crozier', dog='Sasha',
                     size='L', grade=3, rescue=True, collie=True, junior=False,
                     league=league),
               Entry(handler='Peter Crozier', dog='Jack',
                     size='S', grade=4, rescue=False, collie=False,
                     junior=False, league=league),
               Entry(handler='Lindsay Hutchinson', dog='Elvis',
                     size='M', grade=5, rescue=True, collie=False, junior=True,
                     league=league)]
    db.session.add_all(entries)

    course = Course(class_=c1, round=r1, time=29.)
    db.session.add(course)

    for i, e in enumerate(entries[:3]):
        score = Score(course=course, entry=e, faults=i*5, time=30.+i*2.3,
                      eliminated=False)
        db.session.add(score)
        db.session.commit()
    score = Score(course=course, entry=entries[3], eliminated=True)
    db.session.add(score)

    db.session.commit()

    course.update_points()


if __name__ == '__main__':
    import sys
    if '--populate' in sys.argv:
        initialise()
        populate()
    else:
        print('add --populate to add data')
        sys.exit(1)
