
from flask_wtf import Form
from wtforms import (BooleanField, StringField, IntegerField, SubmitField,
                     SelectField, SelectMultipleField, validators)
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

def league_form(league):

    class LeagueForm(Form):

        name = StringField('Name', [validators.InputRequired()])
   
        num_rounds = IntegerField('Number of Rounds',
                                  [validators.NumberRange(min=1),
                                   validators.InputRequired()])

    for i in range(len(league.rounds)):
        setattr(LeagueForm, 'round_{}'.format(i+1),
                DateField('Round {} Date'.format(i+1),
                          [validators.InputRequired()],
                          widget=DatePickerWidget()))
        
    setattr(LeagueForm, 'registration_start',
            DateTimeField('Registration Opens',
                          widget=DateTimePickerWidget()))
    setattr(LeagueForm, 'registration_end',
            DateTimeField('Registration Opens',
                          widget=DateTimePickerWidget()))
    setattr(LeagueForm, 'submit', SubmitField())

    return LeagueForm

class EntryForm(Form):
    handler = StringField('Handler', [validators.InputRequired()])
    dog     = StringField('Dog',     [validators.InputRequired()])
    size    = SelectField('Size', [validators.InputRequired()],
                          choices=[('L', 'Large'),
                                   ('M', 'Medium'),
                                   ('S', 'Small')])
    grade = IntegerField('Grade', [validators.NumberRange(1, 7),
                                   validators.InputRequired()])
    rescue = BooleanField('Rescue Dog')
    abc    = BooleanField('Anything But Collies')
    junior = BooleanField('Junior Handler')
    submit  = SubmitField()
