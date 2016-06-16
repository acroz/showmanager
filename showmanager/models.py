
from .app import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property

class League(db.Model):

    __tablename__ = 'leagues'

    id   = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String)

    registration_start = db.Column(db.DateTime)
    registration_end   = db.Column(db.DateTime)

    last_entry = db.Column(db.DateTime, default=datetime.utcnow)
    numbering_assigned = db.Column(db.DateTime)

    classes = db.relationship('Class', back_populates='league')
    rounds  = db.relationship('Round', order_by='Round.date',
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
    id      = db.Column(db.Integer, primary_key=True)
    date    = db.Column(db.Date, nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    league    = db.relationship('League', back_populates='rounds')

    @property
    def number(self):
        sibling_ids = [round.id for round in self.league.rounds]
        return sibling_ids.index(self.id) + 1

class Class(db.Model):
    __tablename__ = 'classes'
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String)

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    league    = db.relationship('League', back_populates='classes')

class Entry(db.Model):
    __tablename__ = 'entries'
    id      = db.Column(db.Integer, primary_key=True)
    handler = db.Column(db.String)
    dog     = db.Column(db.String)
    size    = db.Column(db.Enum('S', 'M', 'L'))
    grade   = db.Column(db.Integer)
    rescue  = db.Column(db.Boolean)
    collie  = db.Column(db.Boolean)
    junior  = db.Column(db.Boolean)

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    league    = db.relationship('League', back_populates='entries')

    number = db.Column(db.Integer)

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

    league = League(name='Winter League Old',
                    registration_start=datetime(2015, 6, 1),
                    registration_end=datetime(2015, 8, 31))
    db.session.add(league)

    r1 = Round(date=date(2016, 9, 10), league=league)
    r2 = Round(date=date(2016, 9, 17), league=league)
    r3 = Round(date=date(2016, 9, 24), league=league)
    r4 = Round(date=date(2016, 10, 1), league=league)
    r5 = Round(date=date(2016, 10, 8), league=league)
    r6 = Round(date=date(2016, 10, 15), league=league)
    db.session.add_all([r1, r2, r3, r4, r5, r6])

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
                     size='S', grade=4, rescue=False, collie=False, junior=False,
                     league=league),
               Entry(handler='Lindsay Hutchinson', dog='Elvis',
                     size='M', grade=5, rescue=True, collie=False, junior=True,
                     league=league)]
    db.session.add_all(entries)

    db.session.commit()

if __name__ == '__main__':
    import sys
    if '--populate' in sys.argv:
        initialise()
        populate()
    else:
        print('add --populate to add data')
        sys.exit(1)
