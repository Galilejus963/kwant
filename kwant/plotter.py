"""kwant.plotter docstring"""

from math import sqrt, pi, sin, cos, tan
import warnings
import cairo
try:
    import Image
    defaultname = None
    has_pil = True
except:
    defaultname = "plot.pdf"
    has_pil = False

import kwant

__all__ = ['plot', 'Circle', 'Polygon', 'Line', 'Color', 'LineStyle',
           'black', 'white', 'red', 'green', 'blue']

class Color(object):
    """RGBA color.

    Standard Color object that can be used to specify colors in
    `plot`.

    When creating the Color object, the color is specified in an RGBA scheme,
    i.e. by specifying the red (r), green (g) and blue (b) components
    of the color and optionally an alpha channel controlling the transparancy.

    Parameters
    ----------
    r, g, b : float in the range [0, 1]
        specifies the values of the red, green and blue components of the color
    alpha : float in the range [0, 1], optional
        specifies the transparancy, with alpha=0 completely transparent and
        alpha=1 completely opaque (not transparent).
        Defaults to 1 (opaque).

    Examples
    --------
    The color black is specified using

    >>> black = Color(0, 0, 0)

    and white using

    >>> white = Color(1, 1, 1)

    By default, a color is completely opaque (not transparent). Using the
    optional parameter alpha one can specify transparancy. For example,

    >>> black_transp = Color(0, 0, 0, alpha=0.5)

    is black with 50% transparancy.

    """
    def __init__(self, r, g, b, alpha=1.0):
        for val in (r, g, b, alpha):
            if val < 0 or val > 1:
                raise ValueError("r, g, b, and alpha must be in "
                                 "the range [0,1]")
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha

    def _set_color_cairo(self, ctx, fading=None):
        if fading is not None:
            ctx.set_source_rgba(self.r + fading[1] * (fading[0].r - self.r),
                                self.g + fading[1] * (fading[0].g - self.g),
                                self.b + fading[1] * (fading[0].b - self.b),
                                self.alpha + fading[1] *
                                (fading[0].alpha - self.alpha))
        else:
            ctx.set_source_rgba(self.r, self.g, self.b, self.alpha)

black = Color(0, 0, 0)
white = Color(1, 1, 1)
red = Color(1, 0, 0)
green = Color(0, 1, 0)
blue = Color(0, 0, 1)

# TODO: possibly add dashed, etc.
class LineStyle(object):
    """Object for describing a line style. Can be used as a parameter in the
    class `Line`.

    Right now, the LineStyle object only allows to specify the line cap (i.e.
    the shape of the end of the line). In the future might include dashing,
    etc.

    Parameters
    ----------
    lcap : { 'butt', 'round', 'square'}, optional
        Specifies the shape of the end of the line:

        'butt'
           End of the line is rectangular and ends exactly at the end point.
        'round'
           End of the line is rounded, as if a half-circle is drawn around the
           end point.
        'square'
           End of the line is rectangular, but protrudes beyond the end point,
           as if a square was drawn centered at the end point.

        Defaults to 'butt'.
    """
    def __init__(self, lcap="butt"):
        if lcap == "butt":
            self.lcap = cairo.LINE_CAP_BUTT
        elif lcap == "round":
            self.lcap = cairo.LINE_CAP_ROUND
        elif lcap == "square":
            self.lcap = cairo.LINE_CAP_SQUARE
        else:
            raise ValueError("Unknown line cap style "+lcap)

    def _set_props_cairo(self, ctx, reflen):
        ctx.set_line_cap(self.lcap)

class Line(object):
    """Draws a straight line between the two sites connected by a hopping.

    Standard object that can be used to specify how to draw
    a line representing a hopping in `plot`.

    Parameters
    ----------
    lw : float
        line width relative to the reference length (see `plot`)
    lcol : object realizing the "color functionality" (see `plot`)
        line color
    lsty : a LineStyle object
        line style
    """
    def __init__(self, lw, lcol=black, lsty=LineStyle()):
        self.lw = lw
        self.lcol = lcol
        self.lsty = lsty

    def _draw_cairo(self, ctx, pos1, pos2, reflen, fading=None):
        ctx.new_path()
        if self.lw > 0 and self.lcol is not None and self.lsty is not None:
            ctx.set_line_width(self.lw * reflen)
            self.lcol._set_color_cairo(ctx, fading=fading)
            self.lsty._set_props_cairo(ctx, reflen)
            ctx.move_to(pos1[0], pos1[1])
            ctx.line_to(pos2[0], pos2[1])
            ctx.stroke()

class Circle(object):
    """Draw circle with (relative) radius r centered at a site.

    Standard symbol object that can be used with `plot`.
    Sizes are always given in terms of the reference length
    of `plot`.

    Parameters
    ----------
    r : float
       Radius of the circle
    fcol : color_like object or None, optional
       Fill color. If None, the circle is not filled. Defaults to black.
    lw : float, optional
       Line width of the outline. If 0, no outline is drawn.
       Defaults to 0.1.
    lcol : color_like object or None, optional
       Color of the outline. If None, no outline is drawn. Defaults to None.
    lsty : `LineStyle` object
       Line style of the outline. Defaults to LineStyle().
    """
    def __init__(self, r, fcol=black, lw=0.1, lcol=None, lsty=LineStyle()):
        self.r = r
        self.fcol = fcol
        self.lw = lw
        self.lcol= lcol
        self.lsty = lsty

    def _draw_cairo(self, ctx, pos, reflen, fading=None):
        ctx.new_path()

        if self.fcol is not None:
            self.fcol._set_color_cairo(ctx, fading=fading)
            ctx.arc(pos[0], pos[1], self.r * reflen, 0, 2*pi)
            ctx.fill()

        if self.lw > 0 and self.lcol is not None and self.lsty is not None:
            ctx.set_line_width(self.lw * reflen)
            self.lcol._set_color_cairo(ctx, fading=fading)
            self.lsty._set_props_cairo(ctx, reflen)
            ctx.arc(pos[0], pos[1], self.r * reflen, 0, 2*pi)
            ctx.stroke()

class Polygon(object):
    """Draw a regular n-sided polygon centered at a site.

    Standard symbol object that can be used with `plot`.
    Sizes are always given in terms of the reference length
    of `plot`.

    The size of the polygon can be specifed in one of two ways:
     - either by specifying the side length `a`
     - or by demanding that the area of the polygon is equal to a circle
       with radius `size`

    Parameters
    ----------
    n : int
        Number of sides (i.e. `n=3` is a triangle, `n=4` a square, etc.)
    a, size : float, exactly one must be given
        The size of the polygon, either specified by the side length `a`
        or the radius `size` of a circle of equal area.
    angle : float, optional
        Rotate the polygon counter-clockwise by `angle` (specified
        in radians. Defaults to 0.
    fcol : color_like object or None, optional
        Fill color. If None, the polygon is not filled. Defaults to black.
    lw : float, optional
        Line width of the outline. If 0, no outline is drawn.
        Defaults to 0.1.
    lcol : color_like object or None, optional
        Color of the outline. If None, no outline is drawn. Defaults to None.
    lsty : `LineStyle` object
        Line style of the outline. Defaults to LineStyle().
    """
    def __init__(self, n, a=None, size=None,
                 angle=0, fcol=black, lw=0.1, lcol=None, lsty=LineStyle()):
        if ((a is None and size is None) or
            (a is not None and size is not None)):
            raise ValueError("Either sidelength or equivalent circle radius "
                             "must be specified")

        self.n = n
        if a is None:
            # make are of triangle equal to circle of radius size
            a = sqrt(4 * tan(pi / n) / n * pi) * size
        # note: self.rc is the radius of the circumscribed circle
        self.rc = a / (2 * sin(pi / n))
        self.angle = angle
        self.fcol = fcol
        self.lw = lw
        self.lcol = lcol
        self.lsty = lsty

    def _draw_cairo_poly(self, ctx, pos, reflen):
        ctx.move_to(pos[0] + sin(self.angle) * self.rc * reflen,
                    pos[1] + cos(self.angle) * self.rc * reflen)
        for i in xrange(1, self.n):
            phi = i * 2 * pi / self.n
            ctx.line_to(pos[0] + sin(self.angle + phi) * self.rc * reflen,
                        pos[1] + cos(self.angle + phi) * self.rc * reflen)
        ctx.close_path()

    def _draw_cairo(self, ctx, pos, reflen, fading=None):
        ctx.new_path()

        if self.fcol is not None:
            self.fcol._set_color_cairo(ctx, fading=fading)
            self._draw_cairo_poly(ctx, pos, reflen)
            ctx.fill()

        if self.lw > 0 and self.lcol is not None and self.lsty is not None:
            ctx.set_line_width(self.lw * reflen)
            self.lcol._set_color_cairo(ctx, fading=fading)
            self.lsty._set_props_cairo(ctx, reflen)
            self._draw_cairo_poly(ctx, pos, reflen)
            ctx.stroke()


def plot(system, filename=defaultname, fmt=None, a=None,
         width=600, height=None, border=0.1, bcol=white, pos=None,
         symbols=Circle(r=0.3), lines=Line(lw=0.1),
         lead_symbols=-1, lead_lines=-1,
         lead_fading=[0.6, 0.85]):
    """Plot two-dimensional systems (or two-dimensional representations
    of a system).

    `plot` can be used to plot both unfinalized systems derived from
    kwant.builder.Builder, or the corresponding finalized systems.

    The output of `plot` is highly modifyable, as it does not perform
    any drawing itself, but instead lets objects passed by the user
    (or as default parameters) do the actual drawing work. `plot`
    itself does figure out the range of positions occupied by the
    sites, as well as the smallest distance between two sites which
    then serves as a reference length, unless the user specifies
    explicitely a reference length. This reference length is then
    used so that the sizes of symbols or lines are always given relative
    to that reference length. This is particularly advantageous for
    regular lattices, as it makes it easy to specify the area covered
    by symbols, etc.

    The objects that determine `plot`'s behavior are symbol_like
    (symbols representing sites), line_like (lines representing
    hoppings) and color_like (representing colors). The notes below
    explain in detail how to implement custom classes. In most cases
    it is enough to use the predefined standard objects:

    - for symbol_like: `Circle` and `Polygon`
    - for line_like: `Line`
    - for color_like: `Color`.

    `plot` draws both system sites, as well as sites corresponding to the
    leads. For the leads, several copies of the lead unit cell are plotted
    (per default 2), and they are gradually faded towards the background
    color (at least in the default behavior).

    Parameters
    ----------
    system : (un)finalized system
        System to plot. Either an unfinalized Builder
        (instance of `kwant.builder.Builder`)
        or a finalized builder (instance of
        `kwant.builder.FiniteSystem`).
    filename : string or None, optional
        Name of the file the plot should be written to. The format
        of the file can be determined from the suffix (see `fmt`).
        If None, the plot is output on the screen [provided that the
        Python Image Library (PIL) is installed]. Default is
        None if the PIL is installed, and "plot.pdf" otherwise.
    fmt : {"pdf", "ps", "eps", "svg", "png", "jpg", None}, optional
        Format of the output file, if `filename` is not None. If
        `fmt` is None, the format is determined from the suffix of the
        `filename`. Defaults to None.
    a : float, optional
        Reference length. If None, the reference length is determined
        as the smallest nonzero distance between sites. Defaults to None.
    width, height : float or None, optional
        Width and height of the output picture. In units of
        "pt" for the vector graphics formats (pdf, ps, eps, svg)
        and in pixels for the bitmap formats (png, jpg, and output to screen).
        For the bitmap formats, `width` and `height` are rounded to the nearest
        integer. One of `width` and `height` may be None (but not both
        simultaneously). In this case, the unspecified size is chosen to
        fit with the aspect ratio of the plot. If both are specified, the plot
        is centered on the canvas (possibly with increasing the blank borders).
        `width` defaults to 600, and `height` to None.
    border : float, optional
        Size of the blank border around the plot, relative to the
        total size. Defaults to 0.1.
    bcol : color_like, optional
        Background color. Defaults to white.

        (If the plot is saved in a vector graphics format, `white`
        actually corresponds to no background.  This is a bit hacky
        maybe [fading to bcol e.g. still makes a white symbol, not a
        transparant symbol], but then again there is no reason for
        having a white box behind everything)
    pos : callable or None, optional
        When passed a site should return its (2D) position as a numpy array of
        length 2. If None, the method pos() of the site is used.
        Defaults to None.
    symbols : {symbol_like, callable, dict, None}, optional
        Object responsible for drawing the symbols correspodning to sites.
        Either must be a single symbol_like object (the same symbol is drawn
        for every site, regardless of site group), a callable that
        returns a symbol_like object when passed a site, a dictionary
        with site groups as keys and symbol_like as values
        (allowing to specify different symbols for different site groups),
        or None (in which case no symbols are drawn). Instead of
        a symbol_like object the callable or the dict may also return None
        corresponding to no symbol. Defaults to ``Circle(r=0.3)``.

        The standard symbols available are `Circle` and
        `Polygon`.
    lines : {line_like, callable, dict, None}, optional
        Object responsible for drawing the lines representing the
        hoppings between sites. Either a single line_like object
        (the same type of line is drawn for all hoppings), a callable
        that returns a line_like object when passed two sites,
        a dictionary with tuples of two site groups as keys and
        line_like objects as values (allowing to specify different
        line styles for different hoppings; note that if the hopping
        (a, b) is specified, (b, a) needs not be included in the dictionary),
        or None (in which case no hoppings are drawn). Instead of
        a line_like object the callable or the dict may also return None
        corresponding to no line. Defaults to ``Line(lw=0.1)``.

        The standard line available is `Line`.
    lead_symbols : {symbol_like, callable, dict, -1, None}, optional
        Symbols to be drawn for the sites in the leads. The special
        value -1 indicates that `symbols` (which is used for system sites)
        should be used also for the leads. The other possible values are
        as for the system `symbols`.
        Defaults to -1.
    lead_lines : {line_like, callable, dict, -1, None}, optional
        Lines to be drawn for the hoppings in the leads. The special
        value -1 indicates that `lines` (which is used for system hoppings)
        should be used also for the leads. The other possible values are
        as for the system `lines`.
        Defaults to -1.
    lead_fading : list, optional
        The number of entries in the list determines the number of
        lead unit cells that are plotted. The unit cell `i` is then
        faded by the ratio ``lead_fading[i]`` towards the
        background color `bcol`. Here ``lead_fading[i]==0`` implies no fading
        (i.e. the original symbols and lines),
        whereas ``lead_fading[i]==1`` corresponds to the background color.

    Notes
    -----

    `plot` knows three different legitimate classes representing
    symbols (symbol_like), lines (line_like), and colors (color_like).
    In order to serve as a legitimate object for these,
    a class has to implement certain methods. In particular these
    are

    - symbol_like: objects representing symbols for sites::

         _draw_cairo(ctx, pos, reflen[, fading])

      which draws the symbol onto the cairo context `ctx`
      at the position `pos` (passed as a numpy array of length 2).
      `reflen` is the reference length, allowing the symbol to use
      relative sizes. (Note though that `pos` is in **absolute** cairo
      coordinates).

      If the symbol should also be used to draw leads, `_draw_cairo`
      should also take the optional parameter `fading` wich is a tuple
      `(fadecol, percent)` where `fadecol` is the color towards which
      the symbol should be faded, and `percent` is a number between 0
      and 1 indicating the amount of fading, with `percent=0` no
      fading, and `percent=1` fully faded to `fadecol`. Note that
      while "fading" usually will imply color fading, this is not
      required by plot. Anything conceivable is legitimate.

      The module :mod:`plot` provides two standard symbol classes:
      `Circle` and `Polygon`.

    - line_like: objects representing lines for hoppings::

         _draw_cairo(ctx, pos1, pos2, reflen[, fading])

      which draws the something (typically a line of some sort) onto
      the cairo context `ctx` connecting the position `pos1` and
      `pos2` (passed as a numpy arrays of length 2).  `reflen` is the
      reference length, allowing the line to use relative sizes. (Note
      though that `pos1` and `pos2` are in **absolute** cairo
      coordinates).

      If the line should also be used to draw leads, `_draw_cairo`
      should also take the optional parameter `fading` wich is a tuple
      `(fadecol, percent)` where `fadecol` is the color towards which
      the symbol should be faded, and `percent` is a number between 0
      and 1 indicating the amount of fading, with `percent=0` no
      fading, and `percent=1` fully faded to `fadecol`. Note that
      while "fading" usually will imply color fading, this is not
      required by plot. Anything conceivable is legitimate.

      The module :mod:`plot` provides one standard line class: `Line`.

    - color_like: for objects representing colors::

         def _set_color_cairo(ctx[, fading]):

      which sets the current color of the cairo context `ctx`.

      If the color is passed to an object that requires fading in
      order to be applicable for the representation of leads,
      it must also take the optional parameter 'fading' wich is a tuple
      `(fadecol, percent)` where `fadecol` is the color towards which
      the symbol should be faded, and `percent` is a number between 0
      and 1 indicating the amount of fading, with `percent=0` no
      fading, and `percent=1` fully faded to `fadecol`. Note that
      while "fading" usually will imply color fading, this is not
      required by plot. Anything conceivable is legitimate.

      The module :mod:`plot` provides one standard color class:
      `Color`. In addition, a few common colors are predefined
      as instances of `Color`:`black`, `white`, `red`, `green`,
      and `blue`.
    """

    def iterate_lead_sites_builder(system, lead_copies):
        for lead in system.leads:
            if not isinstance(lead, kwant.builder.BuilderLead):
                continue
            sym = lead.builder.symmetry
            shift = sym.which(lead.neighbors[0]) + 1

            for i in xrange(lead_copies):
                for site in lead.builder.sites():
                    yield sym.act(shift + i, site), i

    def iterate_lead_hoppings_builder(system, lead_copies):
        for lead in system.leads:
            if not isinstance(lead, kwant.builder.BuilderLead):
                continue
            sym = lead.builder.symmetry
            shift = sym.which(lead.neighbors[0]) + 1

            for i in xrange(lead_copies):
                for site1, site2 in lead.builder.hoppings():
                    shift1 = sym.which(site1)[0]
                    shift2 = sym.which(site2)[0]
                    if shift1 >= shift2:
                        yield (sym.act(shift + i, site1),
                               sym.act(shift + i, site2),
                               i + shift1, i  + shift2)
                    else:
                        # Note: this makes sure that hoppings beyond the unit
                        #       cell are always ordered such that they are into
                        #       the previous slice
                        yield (sym.act(shift + i - 1, site1),
                               sym.act(shift + i - 1, site2),
                               i - 1 + shift1, i - 1 + shift2)

    def iterate_system_sites_builder(system):
        for site in system.sites():
            yield site

    def iterate_system_hoppings_builder(system):
        for hopping in system.hoppings():
            yield hopping

    def iterate_lead_sites_llsys(system, lead_copies):
        for ilead in xrange(len(system.leads)):
            lead = system.leads[ilead]
            sym = lead.symmetry
            shift = sym.which(system.site(system.lead_neighbor_seqs[ilead][0]))
            shift += 1

            for i in xrange(lead_copies):
                for isite in xrange(lead.slice_size):
                        yield sym.act(shift + i, lead.site(isite)), i

    def iterate_lead_hoppings_llsys(system, lead_copies):
        for ilead in xrange(len(system.leads)):
            lead = system.leads[ilead]
            sym = lead.symmetry
            shift = sym.which(system.site(system.lead_neighbor_seqs[ilead][0]))
            shift += 1

            for i in xrange(lead_copies):
                for isite in xrange(lead.slice_size):
                    for jsite in lead.graph.out_neighbors(isite):
                        # Note: unlike in builder, it is guaranteed
                        #       in the finalized system that hoppings
                        #       beyond the unit cell are in the previous
                        #       "slice"
                        if jsite < lead.slice_size:
                            yield (sym.act(shift + i, lead.site(isite)),
                                   sym.act(shift + i, lead.site(jsite)),
                                   i, i)
                        else:
                            jsite -= lead.slice_size
                            yield (sym.act(shift + i, lead.site(isite)),
                                   sym.act(shift + i - 1, lead.site(jsite)),
                                   i, i - 1)


    def iterate_system_sites_llsys(system):
        for i in xrange(system.graph.num_nodes):
            yield system.site(i)

    def iterate_system_hoppings_llsys(system):
        for i in xrange(system.graph.num_nodes):
            site1 = system.site(i)
            for j in system.graph.out_neighbors(i):
                # Only yield half of the hoppings (as builder does)
                if i < j:
                    yield (site1, system.site(j))


    def iterate_all_sites(system, lead_copies=0):
        for site in iterate_system_sites(system):
            yield site

        for site, ucindx in iterate_lead_sites(system, lead_copies):
            yield site

    def iterate_all_hoppings(system, lead_copies=0):
        for site1, site2 in iterate_system_hoppings(system):
            yield site1, site2

        for site1, site2, i1, i2 in iterate_lead_hoppings(system, lead_copies):
            yield site1, site2

    if isinstance(system, kwant.builder.Builder):
        iterate_system_sites = iterate_system_sites_builder
        iterate_system_hoppings = iterate_system_hoppings_builder
        iterate_lead_sites = iterate_lead_sites_builder
        iterate_lead_hoppings = iterate_lead_hoppings_builder
    elif isinstance(system, kwant.builder.FiniteSystem):
        iterate_system_sites = iterate_system_sites_llsys
        iterate_system_hoppings = iterate_system_hoppings_llsys
        iterate_lead_sites = iterate_lead_sites_llsys
        iterate_lead_hoppings = iterate_lead_hoppings_llsys
    else:
        raise ValueError("Plotting not suported for given system")

    if width is None and height is None:
        raise ValueError("One of width and height must be not None")

    if a is None:
        dist = 0
    else:
        if a > 0:
            dist = a
        else:
            raise ValueError("The distance a must be >0")

    if pos is None:
        pos = lambda site: site.pos

    if fmt is None and filename is not None:
        # Try to figure out the format from the filename
        fmt = filename.split(".")[-1].lower()
    elif fmt is not None and filename is None:
        raise ValueError("If fmt is specified, filename must be given, too")

    if fmt not in [None, "pdf", "ps", "eps", "svg", "png", "jpg"]:
        raise ValueError("Unknwon format " + fmt)

    # Those two need the PIL
    if fmt in [None, "jpg"] and not has_pil:
        raise ValueError("The requested functionality requires the "
                         "Python Image Library (PIL)")

    # symbols and lines may be constant, functions or dicts
    # Here they are wrapped with a function

    if hasattr(symbols, "__call__"):
        fsymbols = symbols
    elif hasattr(symbols, "__getitem__"):
        fsymbols = lambda x : symbols[x]
    else:
        fsymbols = lambda x : symbols

    if hasattr(lines, "__call__"):
        flines = lines
    elif hasattr(lines, "__getitem__"):
        flines = lambda x, y : lines[x,y] if (x,y) in lines else lines[y,x]
    else:
        flines = lambda x, y : lines

    if lead_symbols == -1:
        flsymbols = fsymbols
    elif hasattr(lead_symbols, "__call__"):
        flsymbols = lead_symbols
    elif hasattr(lead_symbols, "__getitem__"):
        flsymbols = lambda x : lead_symbols[x]
    else:
        flsymbols = lambda x : lead_symbols

    if lead_lines == -1:
        fllines = flines
    elif hasattr(lead_lines, "__call__"):
        fllines = lead_lines
    elif hasattr(lines, "__getitem__"):
        fllines = lambda x, y : (lead_lines[x,y]
                                 if (x,y) in lead_lines else lead_lines[y,x])
    else:
        fllines = lambda x, y : lead_lines


    #Figure out the extent of the system
    nsites = 0
    first = True
    for site in iterate_all_sites(system, len(lead_fading)):
        sitepos = pos(site)
        nsites += 1

        if len(sitepos) != 2:
            raise RuntimeError("Only 2 dimensions are supported by plot")

        if first:
            minx = maxx = sitepos[0]
            miny = maxy = sitepos[1]
            first = False
        else:
            minx = min(sitepos[0], minx)
            maxx = max(sitepos[0], maxx)
            miny = min(sitepos[1], miny)
            maxy = max(sitepos[1], maxy)

    if nsites == 0:
        warnings.warn("Empty system. No output generated");
        return

    rangex = (maxx - minx) / (1 - 2 * border)
    rangey = (maxy - miny) / (1 - 2 * border)

    # If the user gave no typical distance between sites, we need to figure it
    # out ourselves
    # (Note: it is enough to consider one copy of the lead unit cell for
    #        figuring out distances, because of the translational symmetry)
    if a is None:
        first = True
        for site1, site2 in iterate_all_hoppings(system, lead_copies=1):

            # TODO: can I assume always numpy?
            sitedist = sqrt((pos(site1)[0] - pos(site2)[0])**2 +
                            (pos(site1)[1] - pos(site2)[1])**2)

            if sitedist > 0:
                if first:
                    dist = sitedist
                    first = False
                else:
                    dist = min(dist, sitedist)

        # If there were no hoppings, then we can only find the distance
        # by checking the distance between all sites (potentially slow)
        if dist == 0:
            warnings.warn("Finding the typical distance automatically"
                          "may be slow!")

            first = True
            # TODO: hm, in this way I will check distances always twice
            # in principle, it would be enoughto go through all sites
            # site2 *after* site1
            # it's only a factor 2 in speed, so not clear if it makes
            # sense to change it
            for site1 in iterate_all_sites(system, lead_copies=1):
                for site2 in iterate_all_sites(system, lead_copies=1):

                    # TODO: can I assume always numpy?
                    sitedist = sqrt((pos(site1)[0] - pos(site2)[0])**2 +
                                    (pos(site1)[1] - pos(site2)[1])**2)

                    if sitedist > 0:
                        if first:
                            dist = sitedist
                            first = False
                        else:
                            dist = min(dist, sitedist)

        # If dist ist still 0, all sites sit at the same spot
        # In this case I can just use any value for dist
        # (rangex and rangey will also be 0 then)
        if dist == 0:
            dist = 1

    # Use the typical distance, if one of the ranges is 0
    # (e.g. in a one-dimensional system)

    if rangex == 0:
        rangex = dist / (1 - 2 * border)
    if rangey == 0:
        rangey = dist / (1 - 2 * border)

    # Compare with the desired dimensions of the plot

    if height is None:
        height = width * rangey / rangex
    elif width is None:
        width = height * rangex / rangey
    else:
        # both width and height specified
        # check in which direction to expand the border
        if width/height > rangex / rangey:
            rangex = rangey * width / height
        else:
            rangey = rangex * height / width

    # Setup cairo
    if fmt == "pdf":
        surface = cairo.PDFSurface(filename, width, height)
    elif fmt == "ps":
        surface = cairo.PSSurface(filename, width, height)
    elif fmt == "eps":
        surface = cairo.PSSurface(filename, width, height)
        surface.set_eps(True)
    elif fmt == "svg":
        surface = cairo.SVGSurface(filename, width, height)
    elif fmt == "png" or fmt == "jpg" or fmt is None:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                     int(round(width)), int(round(height)))

    ctx = cairo.Context(surface)

    # The default background in the image surface is black
    if fmt == "png" or fmt == "jpg" or fmt is None:
        bcol._set_color_cairo(ctx)
        ctx.rectangle(0, 0, int(round(width)), int(round(height)))
        ctx.fill()
    elif bcol is not white:
        # only draw a background rectangle if background color is not white
        bcol._set_color_cairo(ctx)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

    # Setup the coordinate transformation

    # Note: Cairo uses a coordinate system
    #  ---> x     positioned in the left upper corner
    #  |          of the screen.
    #  v y
    #
    # Instead, we use a mathematical coordinate system.

    # TODO: figure out, if file sizes are smaller without transformation
    #       i. e. if we do the transformation ourselves
    scrminx = width * 0.5 * (rangex - (maxx - minx)) / rangex
    scrminy = height * 0.5 * (rangey - (maxy - miny)) / rangey

    ctx.translate(scrminx, height - scrminy)
    ctx.scale(width/rangex, -height/rangey)
    ctx.translate(-minx, -miny)

    # Now draw the system!

    # The lines for the hoppings

    for site1, site2 in iterate_system_hoppings(system):
        line = flines(site1.group, site2.group)

        if line is not None:
            line._draw_cairo(ctx, pos(site1), pos(site2), dist)

    for site1, site2, ucindx1, ucindx2 in \
            iterate_lead_hoppings(system, len(lead_fading)):
        if ucindx1 == ucindx2:
            line = fllines(site1.group, site2.group)

            if line is not None:
                line._draw_cairo(ctx, pos(site1), pos(site2), dist,
                                 fading=(bcol, lead_fading[ucindx1]))
        else:
            if ucindx1 > -1:
                line = fllines(site1.group, site2.group)
                if line is not None:
                    line._draw_cairo(ctx, pos(site1), (pos(site1)+pos(site2))/2,
                                     dist, fading=(bcol, lead_fading[ucindx1]))
            else:
                #one end of the line is in the system
                line = flines(site1.group, site2.group)
                if line is not None:
                    line._draw_cairo(ctx, pos(site1), (pos(site1)+pos(site2))/2,
                                     dist)

            if ucindx2 > -1:
                line = fllines(site2.group, site1.group)
                if line is not None:
                    line._draw_cairo(ctx, pos(site2), (pos(site1)+pos(site2))/2,
                                     dist, fading=(bcol, lead_fading[ucindx2]))
            else:
                #one end of the line is in the system
                line = flines(site2.group, site1.group)
                if line is not None:
                    line._draw_cairo(ctx, pos(site2), (pos(site1)+pos(site2))/2,
                                     dist)
    # the symbols for the sites

    for site in iterate_system_sites(system):
        symbol = fsymbols(site.group)

        if symbol is not None:
            symbol._draw_cairo(ctx, pos(site), dist)

    for site, ucindx in iterate_lead_sites(system,
                                           lead_copies=len(lead_fading)):
        symbol = flsymbols(site.group)

        if symbol is not None:
            symbol._draw_cairo(ctx, pos(site), dist,
                               fading=(bcol, lead_fading[ucindx]))


    # Show or save the picture, if necessary (depends on format)
    if fmt == None:
        im = Image.frombuffer("RGBA",
                              (surface.get_width(), surface.get_height()),
                              surface.get_data(), "raw", "BGRA", 0, 1)
        im.show()
    elif fmt == "png":
        surface.write_to_png(filename)
    elif fmt == "jpg":
        im = Image.frombuffer("RGBA",
                              (surface.get_width(), surface.get_height()),
                              surface.get_data(), "raw", "BGRA", 0, 1)
        im.save(filename, "JPG")