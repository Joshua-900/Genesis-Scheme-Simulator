#include <math.h>
static void rate(const double *u,double *out,int n,double s,double a,double d) {
    const int offsets[4]={-3*n,3*n,-3,3};
    for(int y=1;y<n-1;y++)for(int x=1;x<n-1;x++){
        int i=3*(y*n+x);
        double p=u[i],q=u[i+1],r=u[i+2],v[3];
        for(int c=0;c<3;c++)
            v[c]=u[i+offsets[0]+c]+u[i+offsets[1]+c]+u[i+offsets[2]+c]+u[i+offsets[3]+c];
        for(int k=0;k<4;k++){
            int j=i+offsets[k];
            double dx=u[j]-p,dy=u[j+1]-q,dz=u[j+2]-r;
            double m=s*((dx*dx+dy*dy)+dz*dz);
            v[0]+=m*dx; v[1]+=m*dy; v[2]+=m*dz;
        }
        v[2]+=a*r;
        double tx=q*v[2]-r*v[1],ty=r*v[0]-p*v[2],tz=p*v[1]-q*v[0];
        out[i]=tx+d*(ty*r-tz*q);
        out[i+1]=ty+d*(tz*p-tx*r);
        out[i+2]=tz+d*(tx*q-ty*p);
    }
}
__declspec(dllexport) void tick(double *u,double *buf,int n,double f,double s,double a,double d){
    int m=3*n*n;
    double *v=buf,*k1=buf+m,*k2=buf+2*m,*k3=buf+3*m,*k4=buf+4*m;
    rate(u,k1,n,s,a,d);
    for(int i=0;i<m;i++)v[i]=u[i]+(.5*f)*k1[i];
    rate(v,k2,n,s,a,d);
    for(int i=0;i<m;i++)v[i]=u[i]+(.5*f)*k2[i];
    rate(v,k3,n,s,a,d);
    for(int i=0;i<m;i++)v[i]=u[i]+f*k3[i];
    rate(v,k4,n,s,a,d);
    for(int y=1;y<n-1;y++)for(int x=1;x<n-1;x++){
        int i=3*(y*n+x);
        for(int c=0;c<3;c++){
            int j=i+c;
            u[j]+=(f/6)*(((k1[j]+2*k2[j])+2*k3[j])+k4[j]);
        }
        double z=sqrt((u[i]*u[i]+u[i+1]*u[i+1])+u[i+2]*u[i+2]);
        if(d){u[i]/=z;u[i+1]/=z;u[i+2]/=z;}
    }
}

