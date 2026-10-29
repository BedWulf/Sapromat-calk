"""Генерация схемы нагружения и полностью построенной эпюры на одном рисунке."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def save_scheme_plot(scheme, data, support_left, path, calc_results=None):
    l = data['l']
    fig, ax = plt.subplots(figsize=(9.0, 4.65 if calc_results else 2.8))
    top = 2.5 if calc_results else 0
    ax.plot([0, 4], [top, top], lw=3, color='black')
    wall = 0 if support_left else 4
    ax.plot([wall, wall], [top-.31, top+.40], lw=3, color='black')
    for i in range(6):
        y=top-.28 + i*.12
        ax.plot([wall, wall+(-.12 if support_left else .12)], [y,y+.1],color='black',lw=.9)
    for i in range(5):
        ax.plot([i,i],[top-.08,top-.31],color='black',lw=.9)
        ax.text(i,top-.46,('0' if i==0 else ('l' if i==1 else f'{i}l')),
                ha='center',va='top',fontsize=11)
    for part in scheme:
        for ld in part:
            sign=ld['direction']
            if ld['type']=='force':
                x=ld['position']/l
                ax.annotate('',xy=(x+.25*sign,top+.34),xytext=(x-.25*sign,top+.34),
                            arrowprops=dict(arrowstyle='->',lw=1.7,color='black'))
                ax.text(x,top+.58,f"{ld['count'] if ld['count'] != 1 else ''}P",ha='center',fontsize=11)
            else:
                a,b=ld['start']/l,ld['end']/l
                for j in range(4):
                    x=a+(j+.5)*(b-a)/4
                    ax.annotate('',xy=(x+.09*sign,top+.30),xytext=(x-.09*sign,top+.30),
                                arrowprops=dict(arrowstyle='->',lw=1.3,color='black'))
                ax.text((a+b)/2,top+.58,f"{ld['count'] if ld['count'] != 1 else ''}q",ha='center',fontsize=11)
    if calc_results:
        segments = list(calc_results.values()) if isinstance(calc_results, dict) else list(calc_results)
        values=[v for seg in segments for v in (seg['N_start'],seg['N_end'])]
        maximum=max(max(abs(v) for v in values),1)
        scale=1.40/maximum
        y_zero=0
        ax.axhline(y_zero,xmin=.055,xmax=.945,color='black',lw=.9)
        for k, seg in enumerate(segments):
            a,b=seg['z_start']/l,seg['z_end']/l
            y1,y2=seg['N_start']*scale,seg['N_end']*scale
            ax.plot([a,b],[y1,y2],color='#17699c',lw=2.2)
            ax.fill_between([a,b],[0,0],[y1,y2],color='#17699c',alpha=.08)
            for j in range(1,11):
                x=a+(b-a)*j/11
                y=y1+(y2-y1)*(x-a)/(b-a)
                ax.plot([x,x],[0,y],color='#17699c',alpha=.52,lw=.65)
            if k:
                prev=segments[k-1]
                yprev=prev['N_end']*scale
                if abs(yprev-y1)>1e-8:
                    ax.plot([a,a],[yprev,y1],color='#17699c',lw=1,ls='--')
            for x,y,v in ((a,y1,seg['N_start']),(b,y2,seg['N_end'])):
                ax.plot(x,y,'o',color='#17699c',ms=3)
                ax.text(x+.045,y+(.10 if y>=0 else -.17),f'{v:g}',fontsize=9)
        ax.text(2.9,1.55,'N(z), кН',fontsize=11)
        ax.text(4.34,-.08,'z',fontsize=11)
        ax.set_ylim(-1.9,3.42)
    else:
        ax.set_ylim(-.8,1.1)
    ax.set_xlim(-.5,4.62);ax.axis('off')
    fig.tight_layout(pad=.15)
    fig.savefig(path,dpi=220,bbox_inches='tight')
    plt.close(fig)
