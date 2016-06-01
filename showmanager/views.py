
from flask import render_template, make_response, request
from .app import app
from .models import Entry

from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, A6
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT

@app.route('/entries')
def entries():
    entries = Entry.query.all() 
    return render_template('entries.html', entries=entries)

@app.route('/chits')
def chits():

    tiled = 'tiled' in request.args

    stream = BytesIO()

    canvas = Canvas(stream, pagesize=A4 if tiled else A6)
    canvas.setTitle('Generated Chits')

    styles = getSampleStyleSheet()

    class PageState(object):
        def __init__(self, canvas, tiled):
            self._canvas = canvas
            self._tiled = tiled
            self._divs_per_page = 4 if tiled else 1
            self._position = 0
        def next(self):
            self._position += 1
            if self._position == self._divs_per_page:
                self._canvas.showPage()
                self._position = 0
        def origin(self):
            if self._tiled:
                return [(0, A6[1]), (A6[0], A6[1]), (0, 0), (A6[0], 0)][self._position]
            else:
                return 0,0

    state = PageState(canvas, tiled)
        
    def frame(top, height=30):
        x0, y0 = state.origin()
        frame = Frame(x0 + 30, y0 + A6[1]-top-height, A6[0]-60, height)
        frame.drawBoundary(canvas)
        return frame

    def add_dynamic_fontsize(frame, text, style=styles['Normal']):
        mystyle = ParagraphStyle(name='custom', parent=style)
        content = Paragraph(text, mystyle)
        while not frame.add(content, canvas):
            mystyle.fontSize *= 0.99
            mystyle.leading  *= 0.99
            content = Paragraph(text, mystyle)

    for entry in Entry.query.all():

        f = frame(30, 34)
        title = Paragraph('Chit', styles['Heading1'])
        f.add(title, canvas)

        f = frame(64, 70)
        heading = Paragraph('Handler', styles['Heading3'])
        f.add(heading, canvas)
        add_dynamic_fontsize(f, entry.handler)
        
        f = frame(134, 70)
        heading = Paragraph('Dog', styles['Heading3'])
        f.add(heading, canvas)
        add_dynamic_fontsize(f, entry.dog)

        state.next()

    canvas.save()

    # Get PDF file data
    data = stream.getvalue()
    stream.close()
    
    response = make_response(data)
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = 'filename="chits.pdf"'

    return response
