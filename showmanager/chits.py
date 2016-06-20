"""
Code for generation of chit PDFs
"""

from io import BytesIO

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, A6
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

# Define some constants
MARGIN = 30
WIDTH = A6[0] - 2 * MARGIN # Content width


class TiledCanvas(object):
    """
    Canvas wrapper to enable convenient tiling of reportlab output.

    Parameters
    ----------
    stream : file-like
        A file-like object that the canvas will write to
    pagesize : tuple, optional
        The size, in points, of the page canvas (defaults to A6)
    """

    def __init__(self, stream, pagesize=A6):

        # Initialise the canvas
        self.canvas = Canvas(stream, pagesize=pagesize)
        
        # Store some alignment information for the tiling
        if pagesize == A6:
            self.tiles = [(0, 0)]
        elif pagesize == A4:
            self.tiles = [(0,     A6[1]),
                          (A6[0], A6[1]),
                          (0,     0),
                          (A6[0], 0)]
        else:
            raise ValueError('pagesize not supported')
        
        # Initialise current position
        self.current_tile = 0
    
    def __getattr__(self, attr):
        """
        Map any undefined methods on to the underlying canvas object.
        """
        return getattr(self.canvas, attr)

    def showPage(self):
        """
        Intercepts calls to showPage, shifting the origin as needed.
        """
        
        # Increment the tile counter
        self.current_tile += 1
        
        # Check if we actually need to shift to a new page
        if self.current_tile == len(self.tiles):

            # Move to new page
            self.canvas.showPage()

            # Reset tile counter
            self.current_tile = 0

    def origin(self):
        """
        Get the origin of the current tile.

        Returns
        -------
        tuple
            The origin, in points
        """
        return self.tiles[self.current_tile]


class TiledCanvasPath(object):
    """
    A path wrapper that works with a TiledCanvas to plot on the right page.

    Parameters
    ----------
    canvas : TiledCanvas
        The canvas to draw on
    """
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.path = canvas.beginPath()

    def __getattr__(self, attr):
        """
        Map on to underlying path.
        """
        return getattr(self.path, attr)

    def moveTo(self, x1, y1):
        """
        Offset moveTo calls by the tile origin.
        """
        x0, y0 = self.canvas.origin()
        self.path.moveTo(x0 + x1, y0 + y1)

    def lineTo(self, x1, y1):
        """
        Offset lineTo calls by the tile origin.
        """
        x0, y0 = self.canvas.origin()
        self.path.lineTo(x0 + x1, y0 + y1)

    def draw(self):
        """
        Draw the path.
        """
        self.canvas.drawPath(self.path)


def frame(canvas, top, height=30, horizontal=(0,1), vpad=0, hpad=0):
    """
    Create a Frame on a TiledCanvas.

    Parameters
    ----------
    top : float
        The height of the top of the frame, points
    height : float, optional
        The height of the frame, points
    horizontal : tuple, optional
       The normalised horiztonal interval to place the frame in
    vpad : float, optional
        The vetrical padding inside the frame
    hpad : float, optional
        The horiztonal padding inside the frame
    """

    # Get the canvas origin
    x0, y0 = canvas.origin()

    # Caclulate the available width
    width = A6[0] - (2 * MARGIN)

    # Calculate the start and width of the frame
    x1 = x0 + MARGIN + width * horizontal[0]
    dx = width * (horizontal[1] - horizontal[0])

    # Create and return the frame instance
    frame = Frame(x1, y0 + A6[1] - top - height, dx, height,
                  topPadding=vpad, bottomPadding=vpad,
                  leftPadding=hpad, rightPadding=hpad)

    return frame


def frame_add_text(canvas, frame, text, style):
    """
    Add text to a frame, automatically reducing the font size until it fits.

    Parameters
    ----------
    canvas : Canvas
        The canvas to add the text to
    frame : Frame
        The frame to place the text in
    text : str
        The text to be written
    style : ParagraphStyle
        The text style to use
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
    """
    Draw a horizontal line across a canvas, within the margins.

    Parameters
    ----------
    canvas : TiledCanvas
        The canvas to draw on
    y : float
        The y coordinate to draw the line at
    """
    # Create path
    path = TiledCanvasPath(canvas)
    # Move to starting position
    path.moveTo(MARGIN, y)
    # Draw to end positon
    path.lineTo(A6[0] - MARGIN, y)
    # Draw the page
    path.draw()


def draw_box(canvas, x0, x1, y0, y1):
    """
    Draw a box on a canvas.

    Parameters
    ----------
    canvas : TiledCanvas
        The canvas to draw on
    x0 : float
        The lower x coordinate of the box
    x1 : float
        The upper x coordinate of the box
    y0 : float
        The lower y coordinate of the box
    y1 : float
        The upper y coordinate of the box
    """
    # Create path
    path = TiledCanvasPath(canvas)

    # Create lines
    path.moveTo(x0, y0)
    path.lineTo(x1, y0)
    path.lineTo(x1, y1)
    path.lineTo(x0, y1)
    path.close()

    # Draw the path
    path.draw()


def chits(class_names, entries, tiled=False):
    """
    Generate a PDF of the chits for a set of classes.

    Parameters
    ----------
    class_names : list
        A list of the names of the classes to generate chits for
    entries : list
        A list of Entry objects that chits are to be generated for
    tiled : bool, optional
        Set to True to generate A4 PDFs with the chits tiled
    """
    
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

    # Loop over the class names
    for name in class_names:
    
        # Loop over all entries
        for entry in entries:
    
            # Start at margin
            vpos = MARGIN
    
            # Frame height should be single line height
            hnormal = styles['Normal'].leading
    
            # First row, add dog number and class name
            f = frame(canvas, vpos, hnormal, horizontal=(0,0.5))
            frame_add_text(canvas, f, 'Dog No: {}'.format(entry.number),
                           styles['Normal'])
            f = frame(canvas, vpos, hnormal, horizontal=(0.5,1))
            frame_add_text(canvas, f, name, styles['Right'])
            vpos += hnormal
            
            # Add a divider
            vpos += 4
            draw_hline(canvas, A6[1] - vpos)
            vpos += 4
    
            # Second row, add the handler
            f = frame(canvas, vpos, hnormal)
            frame_add_text(canvas, f, 'Handler: {}'.format(entry.handler),
                           styles['Normal'])
            vpos += hnormal
    
            # Third row, add the dog and extra info
            f = frame(canvas, vpos, hnormal, horizontal=(0,0.75))
            frame_add_text(canvas, f, 'Dog: {}'.format(entry.dog),
                           styles['Normal'])
    
            # Extra info
            f = frame(canvas, vpos, hnormal, horizontal=(0.75,1))
            frame_add_text(canvas, f, entry.hraj1, styles['Right'])
            vpos += hnormal
    
            # Add abit of space 
            vpos += 20

            # Draw scoring boxes
            box_height = 40
            pad = (box_height - styles['Right12'].leading) / 2.
            for i, text in enumerate(['DOG\'S TIME', 'COURSE TIME',
                                      'TIME FAULTS', 'JUMPING FAULTS']):

                # Add a box label
                f = frame(canvas, vpos, box_height, horizontal=(0,0.7),
                          vpad=pad, hpad=10)
                frame_add_text(canvas, f, text, styles['Right12'])
                
                # Add score box
                draw_box(canvas, MARGIN + WIDTH * 0.7, MARGIN + WIDTH,
                                 A6[1] - vpos, A6[1] - vpos - box_height)
                
                vpos += box_height
            
            # Move to bottom
            vpos = A6[1] - 30 - box_height
            f = frame(canvas, vpos, box_height, horizontal=(0,0.7),
                      vpad=pad, hpad=10)
            # Add a box label
            frame_add_text(canvas, f, 'TOTAL FAULTS', styles['Right12'])
            # Add score box
            draw_box(canvas, MARGIN + WIDTH * 0.7, MARGIN + WIDTH,
                             A6[1] - vpos, A6[1] - vpos - box_height)
    
            canvas.showPage()

    canvas.save()

    # Get PDF file data
    data = stream.getvalue()
    stream.close()
    
    # Return PDF data
    return data
