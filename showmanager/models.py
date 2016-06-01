
from .app import db

class Entry(db.Model):

    id      = db.Column(db.Integer, primary_key=True)
    handler = db.Column(db.String)
    dog     = db.Column(db.String)

def initialise():
    """Create the schema"""
    db.create_all()

def populate():
    """
    Temporary for development: Populate some data
    """
    longname = 'really ' * 30
    entries = [Entry(handler='Some guy with a super duper long name',
                     dog='Really ' + longname + 'long name'),
               Entry(handler='Andrew Crozier', dog='Caffrey'),
               Entry(handler='Lynda Crozier', dog='Sasha'),
               Entry(handler='Peter Crozier', dog='Jack'),
               Entry(handler='Lindsay Hutchinson', dog='Elvis')]
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
