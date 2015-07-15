# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Visualization routines using matplotlib
"""

from matplotlib import pyplot as plt
from matplotlib import transforms
from matplotlib.collections import PatchCollection
from matplotlib.patches import Ellipse, RegularPolygon, Rectangle
from numpy import sqrt
import numpy as np
import logging

__all__ = ['CameraDisplay']

logger = logging.getLogger(__name__)


class CameraDisplay:
    """Camera Display using matplotlib.

    Parameters
    ----------
    geometry : `~ctapipe.io.CameraGeometry`
        Definition of the Camera/Image
    axis : `matplotlib.axes.Axes`
        A matplotlib axes object to plot on, or None to create a new one

    Notes
    -----
    Implementation detail: Pixels are rendered as a
    `matplotlib.collections.RegularPolyCollection`, which is the most
    efficient way in matplotlib to display complex pixel shapes.
    """

    def __init__(self, geometry, axes=None, title="Camera"):
        self.axes = axes if axes is not None else plt.gca()
        self.geom = geometry
        self.pixels = None
        self.cmap = plt.cm.jet

        # initialize the plot and generate the pixels as a
        # RegularPolyCollection

        patches = []
        
        for  xx, yy, aa  in zip(self.geom.pix_x.value,
                                self.geom.pix_y.value,
                                np.array(self.geom.pix_area)):
            if self.geom.pix_type.startswith("hex"):
                rr = sqrt(aa*2/3/sqrt(3))
                poly = RegularPolygon((xx, yy), 6, radius=rr,
                                      orientation=np.radians(0),
                                      fill=True)
            else:
                rr = sqrt(aa)
                poly = Rectangle((xx, yy), width=2*rr, height=2*rr,
                                      angle=np.radians(0),
                                      fill=True)
                

            patches.append(poly)
       

        self.pixels = PatchCollection( patches, cmap=self.cmap, linewidth=0 )

        self.axes.add_collection( self.pixels )
        self.axes.set_aspect('equal', 'datalim')        
        self.axes.set_title(title)
        self.axes.set_xlabel("X position ({})".format(self.geom.pix_x.unit))
        self.axes.set_ylabel("Y position ({})".format(self.geom.pix_y.unit))
        self.axes.autoscale_view()
        self.axes.figure.canvas.mpl_connect('pick_event', self._on_pick)
                      
                  

    def _radius_to_size(self, radii):
        """compute radius in screen coordinates and returns the size in
        points^2, needed for the size parameter of
        RegularPolyCollection. This may not be needed if the
        transormations are set up correctly

        """
        return radii * np.pi * 550  # hard-coded for now until better transform
        # return np.pi * radii ** 2

    def set_cmap(self, cmap):
        """ Change the color map """
        self.pixels.set_cmap(cmap)

    def set_image(self, image):
        """
        Change the image displayed on the Camera. 

        Parameters
        ----------
        image: array_like
            array of values corresponding to the pixels in the CameraGeometry.
        """
        if image.shape != self.geom.pix_x.shape:
            raise ValueError("Image has a different shape {} than the"
                             "given CameraGeometry {}"
                             .format(image.shape, self.geom.pix_x.shape))
        self.pixels.set_array(image)
        plt.draw()  # is there a better way to update this?

    def add_ellipse(self, centroid, length, width, angle, asymmetry=0.0,
                    **kwargs):
        """
        plot an ellipse on top of the camera

        Parameters
        ----------
        centroid: (float,float)
            position of centroid
        length: float
            major axis
        width: float
            minor axis
        angle: float
            rotation angle wrt "up" about the centroid, clockwise, in radians
        asymmetry: float
            3rd-order moment for directionality if known
        kwargs:
            any MatPlotLib style arguments to pass to the Ellipse patch

        """
        ellipse = Ellipse(xy=centroid, width=width, height=length,
                          angle=np.degrees(angle), fill=False, **kwargs)
        self.axes.add_patch(ellipse)
        plt.draw()
        return ellipse

    def overlay_moments(self, momparams, **kwargs):
        """ helper to overlay elipse from a `reco.MomentParameters` structure 

        Parameters
        ----------
        self: type
            description
        momparams: `reco.MomentParameters`
            structuring containing Hillas-style parameterization


        """

        self.add_ellipse(centroid=(momparams.cen_x, momparams.cen_y),
                         length=momparams.length,
                         width=momparams.width, angle=momparams.psi,
                         **kwargs)

    def _on_pick(self, event):
        print("EVENT: {} N={}".format(event,event.ind))
