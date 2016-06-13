
from wtforms import (Form, BooleanField, StringField, DateField, DateTimeField,
                     validators)

class ShowForm(Form):
    name = StringField('Name', [validators.DataRequired()])
    start = DateField('Start', [validators.DataRequired()])
    end   = DateField('End', [validators.DataRequired()])
    registration_start = DateTimeField('Registration Opens')
    registration_end   = DateTimeField('Registration Closes')

def entry_form(show):
    """
    Generate an entry form class for this show.
    """

    class EntryForm(Form):
        handler = StringField('Handler', [validators.DataRequired()])
        dog     = StringField('Dog',     [validators.DataRequired()])
        classes = []
    
    for clss in show.classes:
        field = BooleanField(clss.name)
        setattr(EntryForm, clss.id_string, field)
        EntryForm.classes.append(field)

    return EntryForm
