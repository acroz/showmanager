
from .app import db
from datetime import datetime

class Show(db.Model):

    __tablename__ = 'shows'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    start = db.Column(db.Date, nullable=False)
    end   = db.Column(db.Date, nullable=False)
    registration_start = db.Column(db.DateTime)
    registration_end   = db.Column(db.DateTime)

    last_entry = db.Column(db.DateTime, default=datetime.utcnow)
    numbering_assigned = db.Column(db.DateTime)

    @property
    def date_string(self):
        if self.start == self.end:
            return '{:%d/%m/%Y}'.format(self.start)
        else:
            tpl = '{:%d/%m/%Y} - {:%d/%m/%Y}'
            return tpl.format(self.start, self.end)

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
        for clss in self.classes:
            clss.assign_numbering()
        self.numbering_assigned = datetime.utcnow()

class Class(db.Model):
    __tablename__ = 'classes'
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'))
    show    = db.relationship('Show', backref=db.backref('classes', order_by=id))

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
                start=date(2016, 7, 10),
                end=date(2016, 7, 10),
                registration_start=datetime(2016, 6, 1),
                registration_end=datetime(2016, 6, 30))
    show_closed = Show(name='Closed show',
                       start=date(2016, 6, 10),
                       end=date(2016, 6, 10),
                       registration_start=datetime(2016, 5, 1),
                       registration_end=datetime(2016, 5, 30))
    clss = Class(show=show, name='Agility')
    clss_closed = Class(show=show_closed, name='Agility')
    db.session.add_all([show, show_closed, clss, clss_closed])

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
