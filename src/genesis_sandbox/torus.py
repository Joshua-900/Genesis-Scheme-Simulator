"""Live torus surface renderer and picking. Presentation only; no field updates.

Cached sphere tracing supplies visible UV coordinates and normals. Field values
shade that actual surface each frame. NumPy/Pillow keep export and offscreen QA
independent of driver-specific OpenGL availability.
"""
from __future__ import annotations

import numpy as np
from PIL import Image,ImageFilter

from .render import phase_colors

TAU=2*np.pi
MAJOR=2.15
MINOR=.86


def point(u,v):
    u,v=np.asarray(u),np.asarray(v)
    ring=MAJOR+MINOR*np.cos(v)
    return np.stack((ring*np.cos(u),MINOR*np.sin(v),ring*np.sin(u)),axis=-1)


def uv(points):
    x,y,z=np.moveaxis(points,-1,0)
    return np.stack((np.arctan2(z,x)%TAU,np.arctan2(y,np.hypot(x,z)-MAJOR)%TAU),axis=-1)


def rotation(yaw,tilt,roll):
    a,b,c=np.deg2rad([yaw,tilt,roll])
    ry=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    rx=np.array([[1,0,0],[0,np.cos(b),-np.sin(b)],[0,np.sin(b),np.cos(b)]])
    rz=np.array([[np.cos(c),-np.sin(c),0],[np.sin(c),np.cos(c),0],[0,0,1]])
    return rz@rx@ry


def sample(values,u,v):
    """Periodic smooth surface texture with nodes centered in their UV cells."""
    n=len(values);x=u/TAU*n-.5;y=v/TAU*n-.5
    x0,y0=np.floor(x).astype(int),np.floor(y).astype(int)
    fx,fy=x-x0,y-y0
    return ((1-fx)*(1-fy)*values[y0%n,x0%n]+fx*(1-fy)*values[y0%n,(x0+1)%n]
            +(1-fx)*fy*values[(y0+1)%n,x0%n]+fx*fy*values[(y0+1)%n,(x0+1)%n])


class TorusScene:
    def __init__(self,yaw=-24.,tilt=55.,roll=-12.,zoom=1.):
        self.yaw,self.tilt,self.roll,self.zoom=map(float,(yaw,tilt,roll,zoom))
        self._key=None;self.mapping=None

    def camera(self):
        return dict(yaw=self.yaw,tilt=self.tilt,roll=self.roll,zoom=self.zoom)

    def orbit(self,dx,dy):
        self.yaw=(self.yaw+dx)%360
        self.tilt=float(np.clip(self.tilt+dy,12,168))

    def geometry(self,width,height):
        key=(width,height,self.yaw,self.tilt,self.roll,self.zoom)
        if key==self._key:return self.mapping
        transform=rotation(self.yaw,self.tilt,self.roll)
        u,v=np.meshgrid(np.linspace(0,TAU,64,endpoint=False),np.linspace(0,TAU,32,endpoint=False))
        hull=point(u,v).reshape(-1,3)@transform.T
        pixel=max(np.max(np.abs(hull[:,0]))/(.43*width),np.max(np.abs(hull[:,1]))/(.43*height))/self.zoom
        py,px=np.indices((height,width))
        sx=(px+.5-width/2)*pixel;sy=(height/2-py-.5)*pixel
        bound=MAJOR+MINOR
        candidate=sx*sx+sy*sy<bound*bound
        indices=np.flatnonzero(candidate)
        radius=np.sqrt(np.maximum(0,bound*bound-sx.ravel()[indices]**2-sy.ravel()[indices]**2))
        origins=np.stack((sx.ravel()[indices],sy.ravel()[indices],np.full(len(indices),6.)),axis=-1)@transform
        direction=np.array([0.,0.,-1.])@transform
        t=6-radius;end=6+radius
        hit=np.zeros(len(indices),bool);alive=np.ones(len(indices),bool)
        for _ in range(96):
            ids=np.flatnonzero(alive)
            if not len(ids):break
            p=origins[ids]+t[ids,None]*direction
            distance=np.hypot(np.hypot(p[:,0],p[:,2])-MAJOR,p[:,1])-MINOR
            close=distance<2e-4
            hit[ids[close]]=True;alive[ids[close]]=False
            advance=ids[~close]
            t[advance]+=np.maximum(distance[~close],1e-5)
            alive[advance]&=t[advance]<=end[advance]
        selected=np.flatnonzero(hit);pixels=indices[selected]
        p=origins[selected]+t[selected,None]*direction
        coordinates=uv(p)
        rho=np.maximum(np.hypot(p[:,0],p[:,2]),1e-12)
        normal=np.stack((p[:,0]*(1-MAJOR/rho),p[:,1],p[:,2]*(1-MAJOR/rho)),axis=-1)
        normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12)
        normal=normal@transform.T
        light=np.array([-.4,.65,1.]);light/=np.linalg.norm(light)
        half=light+np.array([0.,0.,1.]);half/=np.linalg.norm(half)
        diffuse=np.maximum(normal@light,0)
        specular=np.maximum(normal@half,0)**45
        rim=(1-np.clip(normal[:,2],0,1))**3
        picker=np.full(width*height,-1,dtype=int);picker[pixels]=np.arange(len(pixels))
        self.mapping=dict(width=width,height=height,pixels=pixels,uv=coordinates,normal=normal,
            diffuse=diffuse,specular=specular,rim=rim,picker=picker.reshape(height,width),pixel_size=pixel)
        self._key=key
        return self.mapping

    def pick_screen(self,x,y,width,height,n):
        """Trace the actual cursor ray, without rounding to a preview pixel."""
        if not 0<=x<width or not 0<=y<height:return None
        key=(width,height,self.yaw,self.tilt,self.roll,self.zoom)
        if getattr(self,'_pick_key',None)!=key:
            transform=rotation(self.yaw,self.tilt,self.roll)
            u,v=np.meshgrid(np.linspace(0,TAU,64,endpoint=False),np.linspace(0,TAU,32,endpoint=False))
            hull=point(u,v).reshape(-1,3)@transform.T
            pixel=max(np.max(abs(hull[:,0]))/(.43*width),np.max(abs(hull[:,1]))/(.43*height))/self.zoom
            self._pick_key=key;self._pick_camera=(transform,pixel)
        transform,pixel=self._pick_camera
        sx=(x+.5-width/2)*pixel;sy=(height/2-y-.5)*pixel
        bound=(MAJOR+MINOR)**2-sx*sx-sy*sy
        if bound<0:return None
        origin=np.array([sx,sy,6.])@transform;direction=-transform[2]
        t=6-np.sqrt(bound);end=6+np.sqrt(bound)
        for _ in range(96):
            p=origin+t*direction
            d=np.hypot(np.hypot(p[0],p[2])-MAJOR,p[1])-MINOR
            if d<2e-4:return tuple((np.floor(uv(p)/TAU*n).astype(int)%n).tolist())
            t+=max(d,1e-5)
            if t>end:return None
        return None

    def pick(self,x,y,n):
        if self.mapping is None:return None
        m=self.mapping
        if not 0<=x<m['width'] or not 0<=y<m['height']:return None
        index=m['picker'][int(y),int(x)]
        if index<0:return None
        return tuple((np.floor(m['uv'][index]/TAU*n).astype(int)%n).tolist())

    def render(self,state,field='theta',width=640,height=640,seams=False):
        m=self.geometry(width,height);n=len(state['theta'])
        py,px=np.indices((height,width))
        radius=((px-width*.5)/width)**2+((py-height*.48)/height)**2
        halo=np.exp(-radius*7)
        rgb=np.empty((height,width,3),float)
        rgb[:]=[3,6,13];rgb+=halo[...,None]*np.array([4,8,18])
        # Quiet studio shadow anchors the volume without introducing a simulated floor.
        shadow=np.exp(-((px-width*.5)/(width*.32))**2-((py-height*.88)/(height*.035))**2)
        rgb*=1-.35*shadow[...,None]
        u,v=m['uv'][:,0],m['uv'][:,1]
        col=(np.floor(u/TAU*n).astype(int)%n);row=(np.floor(v/TAU*n).astype(int)%n)
        active=state.get('active',np.ones((n,n),bool))[row,col]
        theta=state['theta'][row,col]
        c=np.clip(sample(state.get('C',np.zeros((n,n))),u,v),0,1)
        activity=np.clip(state.get('activity',np.zeros((n,n)))[row,col]/.15,0,1)
        flash=state.get('flash',np.zeros((n,n)))[row,col]
        phase=sample(np.exp(1j*state['theta']),u,v)
        tint=phase_colors(np.angle(phase)%TAU)
        colors=phase_colors(theta)
        x=u/TAU*n-col-.5;y=v/TAU*n-row-.5
        along=x*np.cos(theta)+y*np.sin(theta)
        across=-x*np.sin(theta)+y*np.cos(theta)
        distance=np.hypot(np.maximum(np.abs(along)-.29,0),across)
        line=np.clip((.083-distance)/.045,0,1)*active
        glow=np.exp(-(distance/.15)**2)*active
        surface=np.array([8.,17.,30.])*(.28+.72*m['diffuse'])[:,None]
        surface+=tint*(.035+.07*m['diffuse'])[:,None]*active[:,None]
        surface+=np.sqrt(c)[:,None]*np.array([8.,12.,25.])*active[:,None]
        surface+=m['specular'][:,None]*np.array([90.,120.,160.])
        surface+=m['rim'][:,None]*np.array([13.,40.,64.])
        if field=='theta':
            surface+=colors*(line*(.70+.28*activity)+glow*.17)[:,None]
            tip=np.exp(-((along-.25)**2+across**2)/.035**2)*active
            surface+=tip[:,None]*50
        else:
            import matplotlib
            value=c if field=='C' else np.clip(sample(state.get('activity',np.zeros((n,n))),u,v)/2,0,1)
            heat=matplotlib.colormaps['magma'](value)[:,:3]*255
            surface+=heat*(.30+.70*m['diffuse'])[:,None]*active[:,None]
        # Vacancy cells retain only a very dim reference surface; no phantom dash.
        surface[~active]*=.25
        event_radius=np.hypot(x,y)
        surface+=np.maximum(flash,0)[:,None]*np.exp(-(event_radius/.3)**2)[:,None]*np.array([45.,70.,100.])
        surface+=np.maximum(-flash,0)[:,None]*np.exp(-((event_radius-.34)/.07)**2)[:,None]*np.array([100.,25.,55.])
        if seams:
            seam=(np.minimum(u,TAU-u)<.014)|(np.minimum(v,TAU-v)<.014)
            surface[seam]=[100,200,245]
        rgb.reshape(-1,3)[m['pixels']]=surface
        base=Image.fromarray(np.clip(rgb,0,255).astype(np.uint8))
        # Display-only bloom. It does not feed back into any state variable.
        hot=Image.fromarray(np.clip(rgb-30,0,255).astype(np.uint8)).resize((max(1,width//3),max(1,height//3)),Image.Resampling.BILINEAR)
        bloom=np.asarray(hot.filter(ImageFilter.GaussianBlur(1.1)).resize((width,height),Image.Resampling.BILINEAR),float)
        return np.ascontiguousarray(np.clip(np.asarray(base,float)+bloom*.35,0,255).astype(np.uint8))
