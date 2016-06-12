
from .app import db

class Show(db.Model):
    __tablename__ = 'shows'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    datestart = db.Column(db.Date)
    dateend   = db.Column(db.Date)

    @property
    def date_string(self):
        if self.datestart == self.dateend:
            return '{:%d/%m/%Y}'.format(self.datestart)
        else:
            tpl = '{:%d/%m/%Y} - {:%d/%m/%Y}'
            return tpl.format(self.datestart, self.dateend)

class Class(db.Model):
    __tablename__ = 'classes'
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'))
    show    = db.relationship('Show', backref=db.backref('classes', order_by=id))

    @property
    def id_string(self):
        return 'class_{}'.format(self.id)

class Registrant(db.Model):
    __tablename__ = 'registrants'
    id      = db.Column(db.Integer, primary_key=True)
    handler = db.Column(db.String)
    dog     = db.Column(db.String)

class Entry(db.Model):
    __tablename__ = 'entries'
    id      = db.Column(db.Integer, primary_key=True)
    registrant_id = db.Column(db.Integer, db.ForeignKey('registrants.id'))
    registrant    = db.relationship('Registrant', backref=db.backref('entries', order_by=id))
    clss_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    clss    = db.relationship('Class', backref=db.backref('entries', order_by=id))

def initialise():
    """Create the schema"""
    db.create_all()

def populate():
    """
    Temporary for development: Populate some data
    """
    from datetime import date
    show = Show(name='Winter League', datestart=date(2016, 6, 10),
                dateend=date(2016, 6, 10))
    clss = Class(show=show, name='Agility')
    db.session.add_all([show, clss])
    longname = 'really ' * 30
    regs = [Registrant(handler='Some guy with a super duper long name',
                       dog='Really ' + longname + 'long name'),
            Registrant(handler='Andrew Crozier', dog='Caffrey'),
            Registrant(handler='Lynda Crozier', dog='Sasha'),
            Registrant(handler='Peter Crozier', dog='Jack'),
            Registrant(handler='Lindsay Hutchinson', dog='Elvis')]
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
