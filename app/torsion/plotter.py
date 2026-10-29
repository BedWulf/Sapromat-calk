"""Масштабные чертежи и эпюры. Работает headless (Agg) внутри Windows EXE."""
import io
import math
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.patches import Arc, FancyArrowPatch, Rectangle
from model import Calculation


def make_figure(c:Calculation) -> Figure:
    s=c.s
    fig=Figure(figsize=(11.5,9.4),dpi=145,facecolor='white')
    ax_s,ax_t,ax_p=fig.subplots(3,1,sharex=True,gridspec_kw={'height_ratios':[1.20,1.65,1.15],'hspace':0.33})
    L=c.coords[-1]
    ax_s.set_ylim(-0.9,2.1)
    ax_s.axis('off')
    ax_s.plot([0,L],[0,0],linewidth=10,color='#73869c',solid_capstyle='butt',zorder=3)
    for x in c.coords:
        ax_s.plot([x,x],[-.22,.22],color='#21344b',lw=1.7,zorder=4)
    # Fixed support represented by an unmistakable hatched wall.
    wall_x=0 if s.fixed=='left' else L
    pad=(-0.06 if s.fixed=='left' else 0.)
    wall=Rectangle((wall_x+pad,-0.52),0.06,1.05,edgecolor='#263647',facecolor='#dce5ee',hatch='///',linewidth=1.3)
    ax_s.add_patch(wall)
    ax_s.text(wall_x,-0.78,'Заделка',ha='left' if s.fixed=='left' else 'right',fontsize=9,color='#263647')
    for i in range(4):
        center=(c.coords[i]+c.coords[i+1])/2
        ax_s.text(center,-0.36,f'{i+1}: ℓ={s.lengths_m[i]:g} м',ha='center',fontsize=9,color='#2e485d')
        ax_s.text(center,-0.60,f'Ø{s.diameter_mm[i]:g} мм; k={s.hole_ratio[i]:g}',ha='center',fontsize=8,color='#5a6474')
        q=s.distributed_knm_per_m[i]
        if abs(q)>1e-11:
            ax_s.plot([c.coords[i]+0.05*s.lengths_m[i],c.coords[i+1]-0.05*s.lengths_m[i]],[1.05,1.05],lw=2,color='#8d55a2')
            # Triangles display the sense of the distributed twisting moment.
            for f in (.25,.5,.75):
                xp=c.coords[i]+f*s.lengths_m[i]
                ax_s.plot([xp], [1.05], marker='>' if q>0 else '<',color='#8d55a2',ms=7)
            ax_s.text(center,1.27,f'm{i+1}={q:+g} кН·м/м',ha='center',fontsize=9,color='#723e88')
    for i,M in enumerate(s.node_moments_knm):
        if abs(M)<1e-12: continue
        x=c.coords[i]
        # Superscript symbol ⊙ / ⊗ fixes convention; arrows in longitudinal diagram are illustrative.
        ax_s.scatter([x],[.32],marker='o',s=70,facecolors='white',edgecolors='#a13e2e',zorder=7)
        ax_s.text(x,.59,f'M{i}={M:+g}',ha='center',fontsize=9,fontweight='bold',color='#a13e2e',bbox={'facecolor':'white','edgecolor':'none','pad':1})
        ax_s.text(x,.31,'+' if M>0 else '−',ha='center',va='center',fontsize=10,color='#a13e2e',zorder=9)
    ax_s.text(L/2,1.87,'РАСЧЁТНАЯ СХЕМА   (+ — момент по правилу правого винта вдоль +z)',ha='center',fontsize=11,fontweight='bold',color='#15263c')
    # Torque curve: hatch + exact steps at concentrated moments.
    ax_t.axhline(0,color='#40556e',linewidth=1.0)
    for i in range(4):
        a,b=c.coords[i],c.coords[i+1]
        X=[a+(b-a)*j/40 for j in range(41)]
        Y=[c.start_T[i]-s.distributed_knm_per_m[i]*(x-a) for x in X]
        ax_t.plot(X,Y,color='#1879b9',linewidth=2.2)
        ax_t.fill_between(X,Y,0,facecolor='#e4f1fb',alpha=.75,edgecolor='#accce3',hatch='|||',linewidth=0)
        ax_t.scatter([a,b],[Y[0],Y[-1]],s=24,color='#1879b9',zorder=8)
        ax_t.text((a+b)/2,(Y[0]+Y[-1])/2, f'{Y[0]:+.2f} → {Y[-1]:+.2f}',fontsize=8,ha='center',va='bottom',bbox={'facecolor':'white','alpha':.75,'edgecolor':'none','pad':1})
    for i in range(1,4):
        if abs(c.start_T[i]-c.end_T[i-1])>1e-11:
            ax_t.plot([c.coords[i],c.coords[i]],[c.end_T[i-1],c.start_T[i]],lw=1.8,color='#d97736',linestyle='--')
    ax_t.set_ylabel('Mк(z), кН·м',fontweight='bold',fontsize=10)
    ax_t.set_title('ЭПЮРА КРУТЯЩЕГО МОМЕНТА',fontsize=11,weight='bold')
    ax_t.grid(color='#dde6ef',linewidth=.8)
    # Phi plot: left or right clamp enforced by exact boundary integration.
    X, _, Phi = c.sampled(55)
    ax_p.axhline(0,lw=1,color='#40556e')
    ax_p.plot(X,[v*180/math.pi for v in Phi],color='#087e73',lw=2.2)
    ax_p.fill_between(X,[v*180/math.pi for v in Phi],0,alpha=.12,color='#17a197')
    ax_p.scatter(c.coords,[v*180/math.pi for v in c.phi_nodes],color='#087e73',s=25,zorder=7)
    for x,p in zip(c.coords,c.phi_nodes):
        ax_p.annotate(f'{p*180/math.pi:+.3f}°',(x,p*180/math.pi),xytext=(2,6),textcoords='offset points',fontsize=8,color='#096359')
    ax_p.set_title('ЭПЮРА УГЛОВ ЗАКРУЧИВАНИЯ',fontsize=11,fontweight='bold')
    ax_p.set_ylabel('φ(z), град',fontsize=10,fontweight='bold')
    ax_p.set_xlabel('z, м',fontsize=10,fontweight='bold')
    ax_p.grid(color='#dde6ef',linewidth=.8)
    for ax in (ax_t,ax_p):
        for x in c.coords:
            ax.axvline(x,color='#b8c8d9',linewidth=.7)
    ax_p.set_xticks(c.coords)
    ax_p.set_xticklabels([f'{x:g}' for x in c.coords])
    margin=L*.075
    ax_s.set_xlim(-margin,L+margin)
    return fig


def save_plot(c:Calculation,path:str):
    fig=make_figure(c)
    fig.savefig(path,dpi=160,facecolor='white',bbox_inches='tight')


def png_bytes(c:Calculation) -> bytes:
    bio=io.BytesIO()
    make_figure(c).savefig(bio,format='png',dpi=105,facecolor='white',bbox_inches='tight')
    return bio.getvalue()
