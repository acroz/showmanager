from .app import db
from datetime import datetime


class League(db.Model):

    __tablename__ = 'leagues'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String)

    registration_start = db.Column(db.DateTime)
    registration_end = db.Column(db.DateTime)

    last_entry = db.Column(db.DateTime, default=datetime.utcnow)
    numbering_assigned = db.Column(db.DateTime)

    scoring_rounds = db.Column(db.Integer)

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

    @property
    def numbering_up_to_date(self):
        if self.last_entry is None or self.numbering_assigned is None:
            return False
        return self.last_entry < self.numbering_assigned

    def assign_numbering(self):
        for i, entry in enumerate(self.entries):
            entry.number = i + 1
        self.numbering_assigned = datetime.utcnow()


class Round(db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    league = db.relationship('League', back_populates='rounds')

    courses = db.relationship('Course', back_populates='round')
    # order_by='Course.clss.name')

    @property
    def number(self):
        sibling_ids = [round.id for round in self.league.rounds]
        return sibling_ids.index(self.id) + 1

    @property
    def name(self):
        return 'Round {}'.format(self.number)

    @property
    def shortname(self):
        return 'R{}'.format(self.number)


class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    league = db.relationship('League', back_populates='classes')

    courses = db.relationship('Course', back_populates='clss')


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

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    league = db.relationship('League', back_populates='entries')

    number = db.Column(db.Integer)

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
    round = db.relationship('Round', back_populates='courses')

    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    clss = db.relationship('Class', back_populates='courses')

    time = db.Column(db.Float)

    points_assigned = db.Column(db.DateTime)

    scores = db.relationship('Score', back_populates='course')

    @property
    def name(self):
        return '{} {}'.format(self.clss.name, self.round.name)

    @property
    def points_up_to_date(self):

        # Check if points have ever been assigned
        if self.points_assigned is None:
            return False

        # Query for time of last updated score
        most_recent = Score.query.filter(Score.course == self) \
                                 .order_by(Score.modified.desc()) \
                                 .first()

        # Case when no scores have been applied
        if most_recent is None:
            # No points assignment to be done
            return True

        # Points are up to date as long as the last points assignment was later
        # than or at the same time as the last modification of any score
        return self.points_assigned >= most_recent.modified

    def update_points(self):

        # Get the current time once to ensure all assigned times here are
        # the same
        now = datetime.now()

        # Get total entrants in league
        n_entrants = Entry.query.filter_by(league=self.round.league) \
                                .count()

        # Assign points in order, with the best dog getting a number of points
        # equal to the number of participants in the league, and each
        # successive dog getting one point less
        for i, s in enumerate(sorted(scores, key=lambda score: score.order)):

            if s.noshow:
                s.points = 0
            elif s.eliminated:
                s.points = 1
            else:
                s.points = n_entrants - i

            s.modified = now

        # Update points counter
        self.points_assigned = now

        db.session.commit()


class Score(db.Model):
    __tablename__ = 'scores'

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'),
                          primary_key=True)
    course = db.relationship('Course', back_populates='scores')

    entry_id = db.Column(db.Integer, db.ForeignKey('entries.id'),
                         primary_key=True)
    entry = db.relationship('Entry', back_populates='scores')

    faults = db.Column(db.Integer)
    time = db.Column(db.Float)
    eliminated = db.Column(db.Boolean, default=False)

    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now)
    points = db.Column(db.Integer)

    @property
    def noshow(self):
        return self.time is None and not self.eliminated

    @property
    def time_faults(self):
        if self.eliminated or self.noshow:
            return None
        time_over = self.time - self.course.time
        return time_over if time_over > 0. else 0.

    @property
    def total_faults(self):
        if self.eliminated or self.noshow:
            return None
        return self.faults + self.time_faults

    @property
    def clear_round(self):
        return self.total_faults == 0

    @property
    def order(self):
        """
        Score for ordering all participants by faults and time.
        """
        if self.noshow:
            return -2e10
        elif self.eliminated:
            return -1e10
        elif self.clear_round:
            return self.time - self.course.time
        else:
            return self.total_faults


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
                    registration_end=datetime(2016, 8, 31),
                    scoring_rounds=4)
    db.session.add(league)

    league_old = League(name='Winter League Old',
                        registration_start=datetime(2015, 6, 1),
                        registration_end=datetime(2015, 8, 31))
    db.session.add(league_old)

    r1 = Round(date=date(2016, 9, 10), league=league)
    r2 = Round(date=date(2016, 9, 17), league=league)
    r3 = Round(date=date(2016, 9, 24), league=league)
    r4 = Round(date=date(2016, 10, 1), league=league)
    r5 = Round(date=date(2016, 10, 8), league=league)
    r6 = Round(date=date(2016, 10, 15), league=league)
    db.session.add_all([r1, r2, r3, r4, r5, r6])

    db.session.add(Round(date=date(2015, 12, 31), league=league_old))

    c1 = Class(name='Agility', league=league)
    c2 = Class(name='Jumping', league=league)
    db.session.add_all([c1, c2])

    longname = 'really ' * 30
    entries = [Entry(handler='Some guy with a super duper long name',
                     dog='Really ' + longname + 'long name',
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

    course = Course(clss=c1, round=r1, time=29.)
    db.session.add(course)

    from datetime import timedelta
    tenmin = timedelta(seconds=60*10)
    for i, e in enumerate(entries[:3]):
        time = datetime.now() - tenmin * i
        score = Score(course=course, entry=e, faults=i*5, time=30.+i*2.3,
                      eliminated=False, created=time, modified=time)
        db.session.add(score)
        db.session.commit()
    score = Score(course=course, entry=entries[3], eliminated=True)
    db.session.add(score)

    db.session.commit()


if __name__ == '__main__':
    import sys
    if '--populate' in sys.argv:
        initialise()
        populate()
    else:
        print('add --populate to add data')
        sys.exit(1)
