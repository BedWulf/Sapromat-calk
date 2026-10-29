"""Эпюра крутящего момента с сохранением оригинальной схемы ОмГТУ (для варианта)."""
from __future__ import annotations
from pathlib import Path
import io
import sys
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.image import imread
from model import Calculation
from plotter import png_bytes

def teacher_png_bytes(c:Calculation) -> bytes:
    if not c.s.teacher_scheme:
        return png_bytes(c)
    asset=Path(__file__).resolve().parent/'assets'/f'scheme_{c.s.teacher_scheme:02}.png'
    if not asset.exists():
        return png_bytes(c)
    fig=Figure(figsize=(10.6,7.0),dpi=140,facecolor='white')
    ax0,ax=fig.subplots(2,1,gridspec_kw={'height_ratios':[.85,1.35],'hspace':.35})
    img=imread(str(asset))
    ax0.imshow(img,aspect='equal')
    ax0.set_axis_off()
    ax0.set_title(f'Исходная схема № {c.s.teacher_scheme} (приложение 2)',fontsize=12)
    ax.axhline(0,color='#263647',linewidth=1.3)
    for i in range(4):
        a,b=c.coords[i:i+2]
        X=[a+(b-a)*j/40 for j in range(41)]
        Y=[c.start_T[i]-c.s.distributed_knm_per_m[i]*(x-a) for x in X]
        ax.plot(X,Y,color='#1767a0',lw=2.6)
        ax.fill_between(X,Y,0,facecolor='#d8ecfb',alpha=.45,hatch='|||',edgecolor='#819dad',lw=0)
        ax.scatter([a,b],[Y[0],Y[-1]],c='#1767a0',s=25,zorder=4)
        ax.annotate(f'{Y[0]:+g}',xy=(a,Y[0]),xytext=(2,8),textcoords='offset points',fontsize=9)
        ax.annotate(f'{Y[-1]:+g}',xy=(b,Y[-1]),xytext=(-19,8),textcoords='offset points',fontsize=9)
    for i in range(1,4):
        ax.axvline(c.coords[i],color='#b6c6d4',lw=.8)
        if abs(c.end_T[i-1]-c.start_T[i])>1e-10:
            ax.plot([c.coords[i]]*2,[c.end_T[i-1],c.start_T[i]],color='#1767a0',lw=2.2)
    ax.set_xticks(c.coords)
    ax.set_xticklabels(['0','l','2l','3l','4l'])
    ax.set_xlim(-.13,c.coords[-1]+.13)
    ax.set_ylabel('Mк(z), кН·м')
    ax.set_xlabel('z, м')
    ax.set_title('Эпюра крутящих моментов',fontsize=12)
    ax.grid(axis='y',alpha=.3)
    b=io.BytesIO()
    fig.savefig(b,format='png',bbox_inches='tight',dpi=145)
    return b.getvalue()
