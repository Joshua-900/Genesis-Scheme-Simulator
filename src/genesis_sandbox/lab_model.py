"""Creative dropout/drop-in variant, retaining the version-1 sandbox intact."""
import copy
import hashlib
from pathlib import Path
import numpy as np

from .model import Sandbox,LANES,ROOT,source_hashes as classic_hashes
from . import vacancies


def source_hashes():
    hashes=classic_hashes()
    for p in (Path(__file__),Path(vacancies.__file__)):
        hashes[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


class LabSandbox(Sandbox):
    def __init__(self,seed=1,n=64):
        super().__init__(seed,n)
        self.events=[];self.drop_probability=0.;self.return_probability=0.
        self.dropped=0;self.arrived=0
        self.turnover_rng=np.random.default_rng(np.random.SeedSequence([seed,31071]))
        self.interaction_rng=np.random.default_rng(np.random.SeedSequence([seed,31072]))
        for state in self.states.values():
            state.update(active=np.ones((n,n),dtype=bool),activity=np.zeros((n,n)),flash=np.zeros((n,n)))

    @classmethod
    def upgrade(cls,model):
        if isinstance(model,cls):return model
        result=cls(model.seed,model.n)
        for name in LANES:
            for key,value in model.states[name].items():result.states[name][key]=value.copy()
        result.parameters=copy.deepcopy(model.parameters);result.update=model.update
        result.edits=copy.deepcopy(model.edits)
        result.events=[dict(kind='paint',**e) for e in model.edits]
        return result

    @property
    def active(self):return self.states[LANES[0]]['active']

    def set_rates(self,drop,restore):
        drop,restore=float(drop),float(restore)
        if not all(np.isfinite(v) and 0<=v<=1 for v in (drop,restore)):
            raise ValueError('Switching probabilities must be finite and between zero and one.')
        self.drop_probability,self.return_probability=drop,restore
        self.events.append(dict(kind='rates',update=self.update,drop=drop,restore=restore))

    def _presence(self,removed,returned,angles):
        for state in self.states.values():
            for key in vacancies.FIELDS:state[key][removed|returned]=0.
            state['theta'][returned]=angles
            state['active'][removed]=False;state['active'][returned]=True
            state['activity'][removed|returned]=0.
            state['flash'][removed]=-1.;state['flash'][returned]=1.
        self.dropped+=int(removed.sum());self.arrived+=int(returned.sum())

    def presence(self,cells,restore=False,angles=None):
        cells=np.asarray(cells,dtype=int).reshape(-1,2)  # x,y
        if len(cells) and (np.any(cells<0) or np.any(cells>=self.n)):
            raise ValueError('Presence edit outside grid.')
        selected=np.zeros((self.n,self.n),dtype=bool)
        selected[cells[:,1],cells[:,0]]=True
        chosen=selected & (~self.active if restore else self.active)
        if not chosen.any():return
        if restore:
            angles=self.interaction_rng.uniform(0,2*np.pi,int(chosen.sum())) if angles is None else np.asarray(angles,float)
            if len(angles)!=int(chosen.sum()) or not np.isfinite(angles).all():raise ValueError('Arrival angles must match new sites.')
            angles=angles%(2*np.pi)
        else:angles=np.empty(0)
        self._presence(np.zeros_like(chosen) if restore else chosen,chosen if restore else np.zeros_like(chosen),angles)
        actual=np.argwhere(chosen)[:,::-1].tolist()
        self.events.append(dict(kind='presence',update=self.update,cells=actual,restore=bool(restore),angles=angles.tolist()))

    def random_presence(self,count=1,restore=False):
        choices=np.argwhere(~self.active if restore else self.active)
        count=min(int(count),len(choices))
        if count<=0:return
        picked=choices[self.interaction_rng.choice(len(choices),count,replace=False)]
        self.presence(picked[:,::-1],restore)

    def presence_brush(self,x,y,radius,restore=False):
        rows,cols=np.indices((self.n,self.n))
        selected=np.hypot(cols-x,rows-y)<radius
        self.presence(np.argwhere(selected)[:,::-1],restore)

    def paint(self,x,y,radius=4.,angle=np.pi/2,mode='turn'):
        super().paint(x,y,radius,angle,mode)
        for state in self.states.values():state['theta'][~state['active']]=0.
        self.events.append(dict(kind='paint',**self.edits[-1]))

    def advance(self,count=1):
        if not isinstance(count,int) or count<0:raise ValueError('Update count must be a nonnegative integer.')
        for _ in range(count):
            for state in self.states.values():state['flash']*=.85
            if self.drop_probability or self.return_probability:
                before=self.active.copy()
                removed=before & (self.turnover_rng.random(before.shape)<self.drop_probability)
                returned=~before & (self.turnover_rng.random(before.shape)<self.return_probability)
                angles=self.turnover_rng.uniform(0,2*np.pi,int(returned.sum()))
                self._presence(removed,returned,angles)
            for name in LANES:
                state=self.states[name];before=state['theta'].copy()
                vacancies.step(state,self.parameters[name])
                state['activity']=np.where(state['active'],np.abs(np.exp(1j*state['theta'])-np.exp(1j*before)),0.)
            self.update+=1

    def recipe(self):
        r=super().recipe()
        r.update(version=2,variant='vacancy-lab',events=copy.deepcopy(self.events),
            source_sha256=source_hashes(),drop_probability=self.drop_probability,return_probability=self.return_probability,
            dropped=self.dropped,arrived=self.arrived,turnover_rng_state=copy.deepcopy(self.turnover_rng.bit_generator.state),
            interaction_rng_state=copy.deepcopy(self.interaction_rng.bit_generator.state),
            vacancy_semantics='Absent nodes have no bonds/triads/retained state. Fixed-grid no-flux holes. Fresh arrivals have shared random theta and zero retained fields. Automatic removals and returns use the previous occupancy simultaneously.')
        return r

    @classmethod
    def replay(cls,r):
        if r.get('format')!='genesis-sandbox' or r.get('version')!=2:raise ValueError('Unsupported lab recipe.')
        if r.get('source_sha256')!=source_hashes():raise ValueError('Recipe dynamics source fingerprints differ from this checkout.')
        model=cls(r['seed'],r['n'])
        if r.get('parameters')!=model.parameters:raise ValueError('Recipe parameters differ from the presets.')
        end=r['update']
        if not isinstance(end,int) or end<0:raise ValueError('Invalid final update.')
        for e in r['events']:
            if not isinstance(e['update'],int) or not model.update<=e['update']<=end:raise ValueError('Events must be time ordered.')
            model.advance(e['update']-model.update)
            if e['kind']=='rates':model.set_rates(e['drop'],e['restore'])
            elif e['kind']=='paint':model.paint(**{k:e[k] for k in ('x','y','radius','angle','mode')})
            elif e['kind']=='presence':model.presence(e['cells'],e['restore'],e['angles'])
            else:raise ValueError('Unknown lab event.')
        model.advance(end-model.update)
        if model.turnover_rng.bit_generator.state!=r['turnover_rng_state']:raise ValueError('Turnover replay diverged.')
        model.interaction_rng.bit_generator.state=copy.deepcopy(r['interaction_rng_state'])
        return model
