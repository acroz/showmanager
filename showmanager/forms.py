
from flask_wtf import Form
from wtforms import BooleanField, StringField, SubmitField, SelectMultipleField, validators
from wtforms.fields.html5 import DateField, DateTimeField
from wtforms.widgets import HTMLString, html_params

class DatePickerWidget(object):

    TEMPLATE = ('<div class="input-group date datepicker">'
                '<input class="form-control" {text}/>'
                '<span class="input-group-addon">'
                '<span class="glyphicon glyphicon-calendar"></span>'
                '</span>'
                '</div>')

    def __call__(self, field, **kwargs):

        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)

        if not field.data:
            field.data = ""
        text = html_params(type='text', value=field.data, **kwargs)

        return HTMLString(self.TEMPLATE.format(text=text))

class DateTimePickerWidget(object):

    TEMPLATE = ('<div class="input-group date datetimepicker">'
                '<input class="form-control" {text}/>'
                '<span class="input-group-addon">'
                '<span class="glyphicon glyphicon-calendar"></span>'
                '</span>'
                '</div>')

    def __call__(self, field, **kwargs):

        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)

        if not field.data:
            field.data = ""
        text = html_params(type='text', value=field.data, **kwargs)

        return HTMLString(self.TEMPLATE.format(text=text))

class ShowForm(Form):
    name = StringField('Name', [validators.DataRequired()])

    start = DateField('Start', [validators.DataRequired()],
                      widget=DatePickerWidget())
    end   = DateField('End',   [validators.DataRequired()],
                      widget=DatePickerWidget())

    registration_start = DateTimeField('Registration Opens', 
                                       widget=DateTimePickerWidget())
    registration_end   = DateTimeField('Registration Closes',
                                       widget=DateTimePickerWidget())
    submit = SubmitField()

def entry_form(show):
    """
    Generate an entry form class for this show.
    """

    class EntryForm(Form):
        handler = StringField('Handler', [validators.DataRequired()])
        dog     = StringField('Dog',     [validators.DataRequired()])
        classes = SelectMultipleField(choices=[(str(c.id), c.name) for c in show.classes])
        submit  = SubmitField()

    return EntryForm
