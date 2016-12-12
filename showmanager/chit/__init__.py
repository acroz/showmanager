from io import BytesIO

from reportlab.lib.pagesizes import A4, A6
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

from .tiledcanvas import TiledCanvas
from .util import MARGIN, WIDTH, frame, frame_add_text, draw_hline, draw_box


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
    styles['Normal'].leading = 20

    # Right aligned font
    right = ParagraphStyle('Right', parent=styles['Normal'])
    right.alignment = TA_RIGHT
    styles.add(right)

    # Smaller sized right aligned font
    right10 = ParagraphStyle('Right12', parent=styles['Right'])
    right10.fontSize = 12
    right10.leading = 14
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
            f = frame(canvas, vpos, hnormal, horizontal=(0, 0.5))
            frame_add_text(canvas, f, 'Dog No: {}'.format(entry.number),
                           styles['Normal'])
            f = frame(canvas, vpos, hnormal, horizontal=(0.5, 1))
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
            f = frame(canvas, vpos, hnormal, horizontal=(0, 0.75))
            frame_add_text(canvas, f, 'Dog: {}'.format(entry.dog),
                           styles['Normal'])

            # Extra info
            f = frame(canvas, vpos, hnormal, horizontal=(0.75, 1))
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
                f = frame(canvas, vpos, box_height, horizontal=(0, 0.7),
                          vpad=pad, hpad=10)
                frame_add_text(canvas, f, text, styles['Right12'])

                # Add score box
                draw_box(canvas, MARGIN + WIDTH * 0.7, MARGIN + WIDTH,
                         A6[1] - vpos, A6[1] - vpos - box_height)

                vpos += box_height

            # Move to bottom
            vpos = A6[1] - 30 - box_height
            f = frame(canvas, vpos, box_height, horizontal=(0, 0.7),
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
