"""
Code for generation of chit PDFs
"""

from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, A6
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT

MARGIN = 30
WIDTH = A6[0] - 2 * MARGIN # Content width

class TiledCanvas(object):
    """
    Canvas wrapper to enabled seamless tiling of generated output.
    """

    def __init__(self, stream, pagesize=A6):
        self.canvas = Canvas(stream, pagesize=pagesize)
        if pagesize == A6:
            self.tiles = [(0, 0)]
        elif pagesize == A4:
            self.tiles = [(0,     A6[1]),
                          (A6[0], A6[1]),
                          (0,     0),
                          (A6[0], 0)]
        self.current_tile = 0
    
    def __getattr__(self, attr):
        return getattr(self.canvas, attr)

    def showPage(self):
        self.current_tile += 1
        if self.current_tile == len(self.tiles):
            self.current_tile = 0
            self.canvas.showPage()

    def origin(self):
        return self.tiles[self.current_tile]

class TiledCanvasPath(object):
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.path = canvas.beginPath()

    def __getattr__(self, attr):
        return getattr(self.path, attr)

    def moveTo(self, x1, y1):
        x0, y0 = self.canvas.origin()
        self.path.moveTo(x0 + x1, y0 + y1)

    def lineTo(self, x1, y1):
        x0, y0 = self.canvas.origin()
        self.path.lineTo(x0 + x1, y0 + y1)

    def draw(self):
        self.canvas.drawPath(self.path)

def frame(canvas, top, height=30, horizontal=(0,1), vpad=0, hpad=0):
    x0, y0 = canvas.origin()
    width = A6[0] - (2 * MARGIN)
    x1 = x0 + MARGIN + width * horizontal[0]
    dx = width * (horizontal[1] - horizontal[0])
    frame = Frame(x1, y0 + A6[1] - top - height, dx, height,
                  topPadding=vpad, bottomPadding=vpad,
                  leftPadding=hpad, rightPadding=hpad)
    return frame

def frame_add_text(canvas, frame, text, style):
    """
    Add text to a frame, automatically reducing the font size until it fits.
    """

    # Initialise a child style
    mystyle = ParagraphStyle(name='custom', parent=style)

    # Prepare the content
    content = Paragraph(text, mystyle)

    # Try to add the text to the frame, reducing font size until it works
    while not frame.add(content, canvas):
        mystyle.fontSize *= 0.99
        mystyle.leading  *= 0.99
        content = Paragraph(text, mystyle)

def draw_hline(canvas, y):
    path = TiledCanvasPath(canvas)
    path.moveTo(MARGIN, y)
    path.lineTo(A6[0] - MARGIN, y)
    path.draw()

def draw_box(canvas, x0, x1, y0, y1):
    path = TiledCanvasPath(canvas)
    path.moveTo(x0, y0)
    path.lineTo(x1, y0)
    path.lineTo(x1, y1)
    path.lineTo(x0, y1)
    path.close()
    path.draw()

def chits(class_names, entries, tiled=False):
    
    # Set up string stream to hold data
    stream = BytesIO()

    # Prepare Canvas
    canvas = TiledCanvas(stream, pagesize=A4 if tiled else A6)
    canvas.setTitle('Generated Chits')

    # Prepare Font Styles
    styles = getSampleStyleSheet()
    
    # Larger Default Font
    styles['Normal'].fontSize = 14
    styles['Normal'].leading  = 20

    # Right aligned font
    right = ParagraphStyle('Right', parent=styles['Normal'])
    right.alignment = TA_RIGHT
    styles.add(right)

    # Smaller sized right aligned font
    right10 = ParagraphStyle('Right12', parent=styles['Right'])
    right10.fontSize = 12
    right10.leading  = 14
    styles.add(right10)

    for name in class_names:
    
        # Loop over all entries
        for entry in entries:
    
            # Start at margin
            vpos = MARGIN
    
            # Frame height should be single line height
            hnormal = styles['Normal'].leading
    
            # First row, add dog number and class name
            f = frame(canvas, vpos, hnormal, horizontal=(0,0.5))
            frame_add_text(canvas, f, 'Dog No: {}'.format(entry.number), styles['Normal'])
            f = frame(canvas, vpos, hnormal, horizontal=(0.5,1))
            frame_add_text(canvas, f, name, styles['Right'])
            vpos += hnormal
            
            # Add a divider
            vpos += 4
            draw_hline(canvas, A6[1] - vpos)
            vpos += 4
    
            # Second row, add the handler
            f = frame(canvas, vpos, hnormal)
            frame_add_text(canvas, f, 'Handler: {}'.format(entry.handler), styles['Normal'])
            vpos += hnormal
    
            # Third row, add the dog and extra info
            f = frame(canvas, vpos, hnormal, horizontal=(0,0.75))
            frame_add_text(canvas, f, 'Dog: {}'.format(entry.dog), styles['Normal'])
    
            # Extra info
            f = frame(canvas, vpos, hnormal, horizontal=(0.75,1))
            frame_add_text(canvas, f, entry.hraj1, styles['Right'])
            vpos += hnormal
    
    
            vpos += 20
            box_height = 40
            pad = (box_height - styles['Right12'].leading) / 2.
            for i, text in enumerate(['DOG\'S TIME', 'COURSE TIME', 'TIME FAULTS',
                                      'JUMPING FAULTS']):
                f = frame(canvas, vpos, box_height, horizontal=(0,0.7), vpad=pad, hpad=10)
                frame_add_text(canvas, f, text, styles['Right12'])
                
                # Add score box
                draw_box(canvas, MARGIN + WIDTH * 0.7, MARGIN + WIDTH,
                                 A6[1] - vpos, A6[1] - vpos - box_height)
                
                vpos += box_height
            
            vpos = A6[1] - 30 - box_height
            f = frame(canvas, vpos, box_height, horizontal=(0,0.7), vpad=pad, hpad=10)
            frame_add_text(canvas, f, 'TOTAL FAULTS', styles['Right12'])
    
            # Add score box
            draw_box(canvas, MARGIN + WIDTH * 0.7, MARGIN + WIDTH,
                             A6[1] - vpos, A6[1] - vpos - box_height)
    
            canvas.showPage()

    canvas.save()

    # Get PDF file data
    data = stream.getvalue()
    stream.close()

    return data
