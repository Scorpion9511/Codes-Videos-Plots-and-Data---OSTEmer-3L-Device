import gdspy as gd
import math

from parameters import p, m

gd_scratch = {'layer':0, 'datatype': 0}
gd_fc = {'layer':1, 'datatype': 1}
gd_cc = {'layer':2, 'datatype': 1}


cdia, tubedia = 0.03*25.5, 0.03*25.5 #tube dia is 0.01", but made it 0.012", (reverted back for making good mold)
p.conedia = cdia*1.6

p.io_xgap = 2.0
p.io_ygap = 2.0
p.io_dia = 0.5
p.io_rows = 10
p.io_cols = 3

m.ch_xgap = p.io_xgap
m.ch_ygap = p.io_ygap
m.ch_w = 0.075 # 75 micro wide channels

def get_ioport_locs(p, xdir):
    # every odd numbered columns is half-y-shifted and has one extra element.
    locs = []
    ncols, nrows = 3, 10
    x0, y0 = 0, 0 #xdir*(-p.L/2+p.bdrypad+p.xgap+p.rad*(ncols/2+2)), 0
    if xdir==0: xdir = 1
    cols = [xdir*x for x in range(-ncols//2+1, ncols//2+1)]
    rows = [y for y in range(-nrows//2+1, nrows//2+1)]
    for i in cols:
        yoffset = 0
        if abs(i%2)!=1: yoffset = p.io_ygap/2
        for j in rows:
            locs.append([x0+i*p.io_xgap, y0+j*p.io_ygap-yoffset])
        if i%2!=1: locs.append([x0+i*p.io_xgap, y0+j*p.io_ygap+yoffset])
    return locs

def get_port(name='port', lname=gd_scratch['layer'], dname=gd_scratch['datatype']):
    global p
    c = gd.Cell(name)
    rad = p.io_dia/2
    port = gd.Round((0, 0), rad, tolerance=0.01)
    return c.add(port)
def ports_arrange(pat, name):
    c = gd.Cell(name)
    _col1 = gd.CellArray(pat, 1, p.io_rows, (0, p.io_ygap), origin=(0, -(int(p.io_rows/2)-0.5)*p.io_ygap))
    _col2 = gd.CellArray(pat, 1, p.io_rows-1, (0, p.io_ygap), origin=(p.io_xgap, -(int(p.io_rows/2)-1)*p.io_ygap))
    if p.io_cols==3:
        _col3 = gd.CellArray(pat, 1, p.io_rows-1, (0, p.io_ygap), origin=(-p.io_xgap, -(int(p.io_rows/2)-1)*p.io_ygap))
        return c.add([_col1, _col2, _col3])
    return c.add([_col1, _col2])

def cross(l, w, name):
    r1 = gd.Rectangle((-l, -w), (l, w))
    r2 = gd.Rectangle((-w, -l), (w, l))
    cross = gd.boolean(r1, r2, 'or')
    ctmp = gd.Cell(name)
    return ctmp.add(cross)
def background(name='bg', lname=gd_scratch['layer'], dname=gd_scratch['datatype']):
    global p
    c = gd.Cell(name)
    pad, wid = 0.5, 0.4
    l, w = p.chip_l/2, p.chip_w/2
    bdry = gd.FlexPath([(-l, -w), (-l, w), (l, w), (l, -w), (-l, -w)], wid/2, gdsii_path=True, layer=lname, datatype=dname)
    cross1, cross2 = cross(pad, wid/4, name+'_amarks'), cross(pad, wid/8, name+'_amarks_close')
    xgap, ygap = 2*l-4*pad, 2*w-4*pad
    amarks = gd.CellArray(cross1, 2, 2, (xgap, ygap), origin=(-xgap/2, -ygap/2))
    xgap, ygap = 1.5*l-2*pad, 1.5*w-2*pad
    amarks1 = gd.CellArray(cross2, 2, 2, (xgap, ygap), origin=(-xgap/2, -ygap/2))
    l, w = 0.9*l, 0.8*w
    #bdry1 = gd.FlexPath([(-l, -w), (-l, w), (l, w), (l, -w), (-l, -w)], wid/4, gdsii_path=True, layer=lname, datatype=dname)
    return c.add([amarks, amarks1, bdry]) #, bdry1])


def extend_ports(to, ys, w, sign, xshift=0, yshift=0):
    # sign=-1 means that we are using right side ports and have
    # to extend to the left side, and also start from the bottom
    # port. that is sign=-1 mirrors sign=1 both in H and V directions
    ex = []
    ex_start, ex_xgap = 1, 0.4
    i = sign*(p.io_rows-1)
    for y in ys:
        plist = []
        if y==0: i-=sign*1; continue
        p0 = sign*(i%2)*p.io_xgap, i*p.io_ygap/2
        p1 = sign*(p.io_xgap+ex_start+abs(i)*ex_xgap), p0[1]
        p2 = p1[0], y
        p3 = sign*to, y
        plist += p0, p1
        if p1!=p2: plist += p2, p3
        else: plist += p3
        plist = [(x[0]+xshift, x[1]+yshift) for x in plist]
        ex.append(gd.FlexPath(plist, w, gdsii_path=True))
        i-=sign*1
    return ex

def makech(l, w, which='fc', xdir=1, suff='1'):
    #c = gd.Cell('channels')
    y1, y2 = m.ch_ygap, -m.ch_ygap
    if which=='fc':
        ch1 = gd.FlexPath([(0, 0), (xdir*l, 0)], w, gdsii_path=True)
        ch2 = gd.FlexPath([(0, -y1), (xdir*l, -y1), (xdir*l, 0)], w, gdsii_path=True)
        ch3 = gd.FlexPath([(0, y1), (xdir*l, y1), (xdir*l, 0)], w, gdsii_path=True)
        ch = gd.boolean(ch1, ch2, 'or')
        ch = gd.boolean(ch, ch3, 'or')
        ctmp = gd.Cell(which+suff+'_chans')
        return ctmp.add(ch)
    if which=='cc':
        extra_factor = 10 # determines how much CC extends over the valve crossing.
        ch1 = gd.FlexPath([(xdir*(-m.ch_xgap-m.ch_w), -m.ch_ygap/2), (xdir*(l+extra_factor*w), -m.ch_ygap/2)], w, gdsii_path=True)
        ch2 = gd.FlexPath([(xdir*(-m.ch_xgap-m.ch_w), +m.ch_ygap/2), (xdir*(l+extra_factor*w), +m.ch_ygap/2)], w, gdsii_path=True)
        ch = gd.boolean(ch1, ch2, 'or')
        ctmp = gd.Cell(which+suff+'_chans')
        return ctmp.add(ch)

def makesupport():
    pass    

def flowcyto(layer='fc'):
    global p
    global m
    lib = gd.GdsLibrary(unit=1e-03, precision=1e-06)

    p.nutgap = 11
    m.ch_l = p.nutgap
    #ch_l, ch_w, ch_ygap, ch_n = p.nutgap, m.ch_l, m.ch_ygap, m.ch_n
    #print(get_ioport_locs(p, 0))
    piz = get_port()
    inarray = ports_arrange(piz, 'inlet_array')
    ioports = gd.CellArray(inarray, 2, 1, (p.nutgap*3, 0), origin=(-p.nutgap*1.5, 0))

    if layer=='fc':
        chfc = makech(m.ch_l, m.ch_w, which='fc')
        chfc1 = makech(m.ch_l, m.ch_w, which='fc', xdir=-1, suff='2')
    else:
        chcc = makech(m.ch_l, m.ch_w, which='cc')
        chcc1 = makech(m.ch_l, m.ch_w, which='cc', xdir=-1, suff='2')

    y = m.ch_ygap
    m.ch_n = 3
    if layer=='fc':
        chfc_ary = gd.CellArray(chfc, 1, m.ch_n, (0, 3*y), origin=(-p.nutgap*1.5+p.io_xgap, -(m.ch_n-1)*3*y/2))
        chfc1_ary = gd.CellArray(chfc1, 1, m.ch_n, (0, 3*y), origin=(+p.nutgap*1.5-p.io_xgap, -(m.ch_n-1)*3*y/2))
        chamber = gd.Rectangle((-0.100, -0.100), (0.100, 0.100))
        ctmp = gd.Cell('chambers')
        ctmp.add(chamber)
        chambers = gd.CellArray(ctmp, 2, m.ch_n, (3.5*2, 2*p.io_xgap), origin=(-3.5, -2*p.io_xgap))
    else:
        chcc_ary = gd.CellArray(chcc, 1, m.ch_n, (0, 3*y), origin=(-p.nutgap*1.5+p.io_xgap, -(m.ch_n-1)*3*y/2))
        chcc1_ary = gd.CellArray(chcc1, 1, m.ch_n, (0, 3*y), origin=(+p.nutgap*1.5-p.io_xgap, -(m.ch_n-1)*3*y/2))

    
    #ys, s, port_ext = [], 1, []
    #if layer=='fc':
    #    ys, s = [5.5*y, 4.5*y, 2.5*y, 1.5*y, -0.5*y, -1.5*y, -3.5*y, -4.5*y], 1
    #    port_ext += extend_ports(p.nutgap/2, ys, m.ch_w, s, xshift=-s*p.nutgap*1.5)
    #    ys, s = [0, -4.5*y, 0, -1.5*y, 0, 1.5*y, 0, 4.5*y], -1
    #    port_ext += extend_ports(p.nutgap/2, ys, m.ch_w, s, xshift=-s*p.nutgap*1.5)
    #if layer=='fc':
    #    ys, s = [-5.5*y, 0, -2.5*y, 0, 0.5*y, 0, 3.5*y], -1
    #    #ys, s = [4.5*y, 3.5*y, 1.5*y, 0.5*y, -1.5*y, -2.5*y, -4.5*y, -5.5*y], -1
    #    port_ext += extend_ports(p.nutgap/2, ys, m.ch_w, s, xshift=-s*p.nutgap*1.5)

    l, w = p.chip_l/2 - 5*0.5, p.chip_w/2 - 2*0.5 
    ident ='240821-flowcyto-'+layer
    text = gd.Text(ident, 0.4, (-l, -w))
    bg = background()
    #bg.add([ioports, chary, chary2, text]+port_ext)
    if layer=='fc':
        bg.add([ioports, chfc_ary, chfc1_ary, chambers, text]) #+port_ext)
    else:
        bg.add([ioports, chcc_ary, chcc1_ary, text]) #+port_ext)
    lib.add(bg)
    lib.write_gds(ident+'.gds')

#flowcyto(layer='fc')
flowcyto(layer='cc')