
from .app import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property

class Show(db.Model):

    __tablename__ = 'shows'

    id   = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String)
    registration_start = db.Column(db.DateTime)
    registration_end   = db.Column(db.DateTime)

    last_entry = db.Column(db.DateTime, default=datetime.utcnow)
    numbering_assigned = db.Column(db.DateTime)

    days = db.relationship('ShowDay', order_by='ShowDay.date',
                           back_populates='show')
    league_classes = db.relationship('Class', back_populates='league')

    @property
    def date_string(self):
        if len(self.days) == 1:
            return '{:%d/%m/%Y}'.format(self.days[0].date)
        else:
            tpl = '{:%d/%m/%Y} - {:%d/%m/%Y}'
            return tpl.format(self.days[0].date, self.days[-1].date)

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

    @property
    def classes(self):
        for day in self.days:
            for clss in day.classes:
                yield clss
        for clss in self.league_classes:
            yield clss

    def assign_numbering(self):
        for clss in self.classes:
            clss.assign_numbering()
        self.numbering_assigned = datetime.utcnow()

class ShowDay(db.Model):
    __tablename__ = 'showdays'
    id      = db.Column(db.Integer, primary_key=True)
    date    = db.Column(db.Date, nullable=False)

    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'))
    show    = db.relationship('Show', back_populates='days')

    classes = db.relationship('Class', back_populates='day')

class Class(db.Model):
    __tablename__ = 'classes'
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String)
    
    # One-off classes are linked to a day
    day_id = db.Column(db.Integer, db.ForeignKey('showdays.id'))
    day    = db.relationship('ShowDay', back_populates='classes')

    league_id = db.Column(db.Integer, db.ForeignKey('shows.id'))
    league    = db.relationship('Show', back_populates='league_classes')

    @property
    def show(self):
        if self.league is not None:
            return self.league
        else:
            return self.day.show

    def assign_numbering(self):
        query = Entry.query.join(Registrant) \
                           .filter(Entry.clss == self) \
                           .order_by(Registrant.handler)
        for i, entry in enumerate(query.all()):
            entry.number = i + 1

class Registrant(db.Model):
    __tablename__ = 'registrants'
    id      = db.Column(db.Integer, primary_key=True)
    handler = db.Column(db.String)
    dog     = db.Column(db.String)
    size    = db.Column(db.Enum('S', 'M', 'L'))
    grade   = db.Column(db.Integer)
    rescue  = db.Column(db.Boolean)
    collie  = db.Column(db.Boolean)
    junior  = db.Column(db.Boolean)

class Entry(db.Model):
    __tablename__ = 'entries'
    id      = db.Column(db.Integer, primary_key=True)
    registrant_id = db.Column(db.Integer, db.ForeignKey('registrants.id'))
    registrant    = db.relationship('Registrant', backref=db.backref('entries', order_by=id))
    clss_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    clss    = db.relationship('Class', backref=db.backref('entries', order_by=id))
    number = db.Column(db.Integer)

def initialise():
    """Create the schema"""
    db.create_all()

def populate():
    """
    Temporary for development: Populate some data
    """
    from datetime import date, datetime

    show = Show(name='Winter League',
                registration_start=datetime(2016, 6, 1),
                registration_end=datetime(2016, 6, 30))
    wld1 = ShowDay(show=show, date=date(2016, 7, 10))
    wld2 = ShowDay(show=show, date=date(2016, 7, 17))
    wld3 = ShowDay(show=show, date=date(2016, 7, 24))
    db.session.add_all([show, wld1, wld2, wld3])

    show_closed = Show(name='Closed show',
                       registration_start=datetime(2016, 5, 1),
                       registration_end=datetime(2016, 5, 30))
    cld1 = ShowDay(show=show_closed, date=date(2016, 6, 10))
    cld2 = ShowDay(show=show_closed, date=date(2016, 6, 11))
    db.session.add_all([show_closed, cld1, cld2])

    clss = Class(league=show, name='Agility')
    clss_closed = Class(day=cld1, name='Agility')
    jumping = Class(league=show, name='Jumping')
    db.session.add_all([clss, clss_closed, jumping])

    longname = 'really ' * 30
    regs = [Registrant(handler='Some guy with a super duper long name',
                       dog='Really ' + longname + 'long name',
                       size='S', grade=1, rescue=True, collie=False, junior=True),
            Registrant(handler='Andrew Crozier', dog='Caffrey',
                       size='M', grade=2, rescue=False, collie=True, junior=True),
            Registrant(handler='Lynda Crozier', dog='Sasha',
                       size='L', grade=3, rescue=True, collie=True, junior=False),
            Registrant(handler='Peter Crozier', dog='Jack',
                       size='S', grade=4, rescue=False, collie=False, junior=False),
            Registrant(handler='Lindsay Hutchinson', dog='Elvis',
                       size='M', grade=5, rescue=True, collie=False, junior=True)]
    entries = [Entry(registrant=r, clss=clss) for r in regs]
    entries += [Entry(registrant=r, clss=jumping) for r in regs[2:]]
    entries += [Entry(registrant=r, clss=clss_closed) for r in regs[:4]]
    db.session.add_all(entries + regs)

    db.session.commit()

if __name__ == '__main__':
    import sys
    if '--populate' in sys.argv:
        initialise()
        populate()
    else:
        print('add --populate to add data')
        sys.exit(1)
