
from wtforms import Form, BooleanField, StringField, validators

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
