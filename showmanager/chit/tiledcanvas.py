from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, A6


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
