from reportlab.lib.pagesizes import A6
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle

from .tiledcanvas import TiledCanvasPath

# Define some constants
MARGIN = 30
WIDTH = A6[0] - 2 * MARGIN  # Content width


def frame(canvas, top, height=30, horizontal=(0, 1), vpad=0, hpad=0):
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
        mystyle.leading *= 0.99
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
