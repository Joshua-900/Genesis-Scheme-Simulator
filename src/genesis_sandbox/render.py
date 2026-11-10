"""Procedural luminous dash rendering, separate from the field dynamics."""
import numpy as np
from PIL import Image


def phase_colors(theta):
    colors=np.array([[66,245,220],[147,147,255],[255,132,111],[255,217,136],[66,245,220]],float)
    t=(theta%(2*np.pi))/(2*np.pi)*4
    index=np.floor(t).astype(int)
    fraction=(t-index)[...,None]
    return colors[index]*(1-fraction)+colors[index+1]*fraction


def dash_pixels(state,scale=8,zoom=1):
    n=len(state['theta']);side=n*scale
    py,px=np.indices((side,side))
    span=n/zoom
    sx=(n-span)/2+(px+.5)/side*span
    sy=(n-span)/2+(py+.5)/side*span
    cols=np.floor(sx).astype(int);rows=n-1-np.floor(sy).astype(int)
    x=sx-np.floor(sx)-.5
    y=.5-(sy-np.floor(sy))
    theta=state['theta'][rows,cols]
    active=state.get('active',np.ones((n,n),bool))[rows,cols]
    c=np.clip(state.get('C',np.zeros((n,n)))[rows,cols],0,1)
    activity=np.clip(state.get('activity',np.zeros((n,n)))[rows,cols]/.15,0,1)
    flash=state.get('flash',np.zeros((n,n)))[rows,cols]
    along=x*np.cos(theta)+y*np.sin(theta)
    across=-x*np.sin(theta)+y*np.cos(theta)
    distance=np.hypot(np.maximum(np.abs(along)-.255,0),across)
    core=np.clip((.09-distance)/.055,0,1)*active
    glow=np.exp(-(distance/.16)**2)*.22*active
    colors=phase_colors(theta)
    rgb=np.empty((side,side,3));rgb[:]=[3,8,15]
    rgb+=np.sqrt(c)[...,None]*np.array([3,4,10])*active[...,None]
    rgb+=colors*(glow+core*(.72+.20*activity))[...,None]
    tip=np.exp(-((along-.24)**2+across**2)/.035**2)*active
    rgb+=tip[...,None]*np.array([75,75,75])
    radius=np.hypot(x,y)
    arrival=np.maximum(flash,0)*np.exp(-(radius/.34)**2)
    departure=np.maximum(-flash,0)*np.exp(-((radius-.34)/.065)**2)
    rgb+=arrival[...,None]*np.array([32,50,70])+departure[...,None]*np.array([90,28,48])
    return np.ascontiguousarray(np.clip(rgb,0,255).astype(np.uint8))


def image(state,field='theta',style='dashes',side=640,zoom=1,camera=None,seams=False):
    if style=='torus':
        from .torus import TorusScene
        return Image.fromarray(TorusScene(**(camera or {})).render(state,field,side,side,seams))
    if style=='dashes' and field=='theta':
        rgb=dash_pixels(state,max(4,int(np.ceil(side/len(state['theta'])))),zoom)
    else:
        from .export import pixels
        rgb=pixels(state,field)
    result=Image.fromarray(rgb)
    if zoom!=1 and not (style=='dashes' and field=='theta'):
        width=result.width;crop=width/zoom
        result=result.crop(((width-crop)/2,(width-crop)/2,(width+crop)/2,(width+crop)/2))
    return result.resize((side,side),Image.Resampling.LANCZOS if style=='dashes' and field=='theta' else Image.Resampling.NEAREST)
