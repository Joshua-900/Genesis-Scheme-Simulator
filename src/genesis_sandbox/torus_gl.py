"""Optional GPU presentation; software renderer remains the export/fallback path."""
from __future__ import annotations

import logging
import numpy as np
from vispy import app,gloo
from .torus import rotation,point,TAU

VERTEX='''
attribute vec2 position;
void main(){gl_Position=vec4(position,0.,1.);}
'''
FRAGMENT='''
uniform vec2 size;
uniform vec3 right;
uniform vec3 up;
uniform vec3 eye;
uniform float pixel;
uniform float n;
uniform float mode;
uniform float seams;
uniform sampler2D field;
uniform sampler2D events;
uniform sampler2D palette;
const float TAU=6.28318530718;
float sdf(vec3 p){return length(vec2(length(p.xz)-2.15,p.y))-.86;}
vec3 color(float a){
 float q=mod(a/TAU,1.)*4.;
 if(q<1.)return mix(vec3(66,245,220),vec3(147,147,255),q);
 if(q<2.)return mix(vec3(147,147,255),vec3(255,132,111),q-1.);
 if(q<3.)return mix(vec3(255,132,111),vec3(255,217,136),q-2.);
 return mix(vec3(255,217,136),vec3(66,245,220),q-3.);
}
void main(){
 vec2 screen=(gl_FragCoord.xy-size*.5)*pixel;
 vec2 normalized=gl_FragCoord.xy/size-.5;
 vec3 bg=vec3(3,6,13)+exp(-dot(normalized,normalized)*7.)*vec3(4,8,18);
 vec3 rgb=bg;
 float rad=3.01*3.01-dot(screen,screen);
 if(rad>0.){
  vec3 origin=screen.x*right+screen.y*up+6.*eye;
  vec3 dir=-eye;
  float t=6.-sqrt(rad),end=6.+sqrt(rad);
  bool hit=false;vec3 p;
  for(int i=0;i<96;i++){
   p=origin+t*dir;float d=sdf(p);
   if(d<.0002){hit=true;break;}
   t+=max(d,.00001);if(t>end)break;
  }
  if(hit){
   float rho=length(p.xz);
   vec3 normal=normalize(vec3(p.x*(1.-2.15/rho),p.y,p.z*(1.-2.15/rho)));
   normal=vec3(dot(normal,right),dot(normal,up),dot(normal,eye));
   vec3 light=normalize(vec3(-.4,.65,1.));
   float diffuse=max(dot(normal,light),0.);
   float spec=pow(max(dot(normal,normalize(light+vec3(0,0,1))),0.),45.);
   float rim=pow(1.-clamp(normal.z,0.,1.),3.);
   vec2 uv=mod(vec2(atan(p.z,p.x),atan(p.y,rho-2.15))/TAU,1.);
   vec2 cell=floor(uv*n),center=(cell+.5)/n;
   vec4 smoothfield=texture2D(field,uv),local=texture2D(field,center);
   vec4 event=texture2D(events,center);
   float theta=mod(atan(local.y,local.x),TAU),occupied=local.a;
   vec2 xy=uv*n-cell-.5;
   float along=dot(xy,vec2(cos(theta),sin(theta)));
   float across=dot(xy,vec2(-sin(theta),cos(theta)));
   float d=length(vec2(max(abs(along)-.29,0.),across));
   float line=clamp((.083-d)/.045,0.,1.)*occupied;
   float glow=exp(-pow(d/.15,2.))*occupied;
   rgb=vec3(8,17,30)*(.28+.72*diffuse);
   rgb+=color(mod(atan(smoothfield.y,smoothfield.x),TAU))*(.035+.07*diffuse)*occupied;
   rgb+=sqrt(clamp(smoothfield.z,0.,1.))*vec3(8,12,25)*occupied;
   rgb+=spec*vec3(90,120,160)+rim*vec3(13,40,64);
   if(mode<.5){
    rgb+=color(theta)*(line*(.70+.28*clamp(event.x/.15,0.,1.))+glow*.24);
    rgb+=exp(-((along-.25)*(along-.25)+across*across)/(.035*.035))*occupied*50.;
   }else{
    float value=mode<1.5?clamp(smoothfield.z,0.,1.):clamp(texture2D(events,uv).x/2.,0.,1.);
    rgb+=texture2D(palette,vec2(value,.5)).rgb*255.*(.3+.7*diffuse)*occupied;
   }
   if(occupied<.5)rgb*=.25;
   float r=length(xy);
   rgb+=max(event.y,0.)*exp(-pow(r/.3,2.))*vec3(45,70,100);
   rgb+=max(-event.y,0.)*exp(-pow((r-.34)/.07,2.))*vec3(100,25,55);
   if(seams>.5 && (min(uv.x,1.-uv.x)<.00223 || min(uv.y,1.-uv.y)<.00223))rgb=vec3(100,200,245);
  }
 }
 gl_FragColor=vec4(clamp(rgb/255.,0.,1.),1.);
}
'''


class TorusGPU(app.Canvas):
    def __init__(self,parent,failure):
        super().__init__(parent=parent,keys=None,app='pyqt5',vsync=True)
        self.failure=failure;self.ready=False
        self.program=gloo.Program(VERTEX,FRAGMENT)
        self.program['position']=np.array([[-1,-1],[1,-1],[-1,1],[1,1]],np.float32)
        import matplotlib
        lut=np.asarray(matplotlib.colormaps['magma'](np.linspace(0,1,256))[:,:3],np.float32)[None,:,:]
        self.program['palette']=gloo.Texture2D(lut,interpolation='linear')
        self.field_texture=None;self.events_texture=None

    def set_field(self,state,field,scene,seams):
        theta=state['theta'];n=len(theta)
        data=np.stack((np.cos(theta),np.sin(theta),state['C'],state['active']),axis=-1).astype(np.float32)
        meta=np.zeros((n,n,4),np.float32);meta[:,:,0]=state['activity'];meta[:,:,1]=state['flash']
        if self.field_texture is None:
            self.field_texture=gloo.Texture2D(data,interpolation='linear',wrapping='repeat')
            self.events_texture=gloo.Texture2D(meta,interpolation='linear',wrapping='repeat')
            self.program['field']=self.field_texture;self.program['events']=self.events_texture
        else:self.field_texture.set_data(data);self.events_texture.set_data(meta)
        self.program['n']=float(n);self.program['mode']=float(('theta','C','activity').index(field))
        self.program['seams']=float(seams)
        self.ready=True;self.set_camera(scene)

    def set_camera(self,scene):
        w,h=self.physical_size
        if not w or not h:return
        transform=rotation(scene.yaw,scene.tilt,scene.roll)
        u,v=np.meshgrid(np.linspace(0,TAU,64,endpoint=False),np.linspace(0,TAU,32,endpoint=False))
        hull=point(u,v).reshape(-1,3)@transform.T
        pixel=max(np.max(abs(hull[:,0]))/(.43*w),np.max(abs(hull[:,1]))/(.43*h))/scene.zoom
        self.program['size']=(float(w),float(h));self.program['pixel']=float(pixel)
        for name,row in zip(('right','up','eye'),transform):self.program[name]=row.astype(np.float32)
        self.update()

    def on_draw(self,event):
        if not self.ready:return
        try:
            gloo.set_viewport(0,0,*self.physical_size)
            gloo.set_state(depth_test=False,blend=False,cull_face=False)
            gloo.clear(color=(.01,.02,.04,1.))
            self.program.draw('triangle_strip')
        except Exception:
            logging.exception('Torus GPU failed; falling back to software')
            self.ready=False;self.failure()

