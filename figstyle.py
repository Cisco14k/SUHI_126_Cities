import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MM = 1 / 25.4
W2 = 183 * MM     # double column
W1 = 89 * MM      # single column
# Nature Publishing Group (NPG) palette anchors (#00A087 green, #E64B35 red, #4DBBD5 cyan, #3C5488 navy, #7E6148 brown),
# adjusted where needed to pass lightness/chroma/colour-vision checks (dataviz validator); markers give secondary encoding.
NPG = dict(green='#00A087', red='#E64B35', cyan='#4DBBD5', navy='#3C5488', blue='#3B5FB0', brown='#7E6148', grey='#7F7F7F',
           gold='#D9A400', lime='#8DB600', purple='#6A51A3', salmon='#F39B7F')
SRC_COL = {'tree': NPG['green'], 'grass': NPG['lime'], 'water': NPG['blue'], 'bare': NPG['brown']}
SRC_LAB = {'tree': 'Tree canopy', 'grass': 'Open green space', 'water': 'Water', 'bare': 'Bare ground'}
SRC_MK = {'tree': 'o', 'grass': 's', 'water': 'D', 'bare': '^'}
ZONE_COL = {'Tropical': NPG['red'], 'Arid': NPG['gold'], 'Temperate': NPG['cyan'], 'Continental': NPG['purple']}
ZONE_MK = {'Tropical': 'o', 'Arid': '^', 'Temperate': 's', 'Continental': 'D'}
DEC_COL = ['#BFC8E3', '#8C9CCB', '#5A6FAE', '#2B3D73']     # sequential NPG navy ramp (light -> dark)
INK = '#222222'; INK2 = '#555555'; GRID = '#E5E5E5'; FILL = '#F2F2F2'


def setup():
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'Liberation Sans', 'DejaVu Sans'],
        'font.size': 7, 'axes.titlesize': 7, 'axes.labelsize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
        'legend.fontsize': 6.5, 'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
        'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'axes.edgecolor': INK2, 'axes.labelcolor': INK,
        'xtick.color': INK2, 'ytick.color': INK2, 'text.color': INK, 'axes.spines.top': False, 'axes.spines.right': False,
        'legend.frameon': False, 'savefig.dpi': 300, 'figure.dpi': 150, 'lines.linewidth': 1.2, 'axes.titleweight': 'bold',
        'axes.titlelocation': 'left', 'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none', 'mathtext.fontset': 'custom',
        'mathtext.rm': 'Liberation Sans', 'mathtext.it': 'Liberation Sans:italic', 'mathtext.bf': 'Liberation Sans:bold'})


def panel(ax, letter, x=-0.16, y=1.04):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=8, fontweight='bold', va='bottom', ha='left')


def zero(ax):
    ax.axhline(0, color=INK2, lw=0.5, zorder=0)


def save(fig, path):
    """PNG (300 dpi) for the manuscript file and an editable vector PDF for submission."""
    fig.savefig(path, dpi=300)
    fig.savefig(path.rsplit('.', 1)[0] + '.pdf')

from matplotlib.colors import LinearSegmentedColormap
CANOPY_CMAP = LinearSegmentedColormap.from_list('npg_green', ['#FFFFFF', '#BFE6DD', '#00A087', '#00513F'])
DIV_CMAP = LinearSegmentedColormap.from_list('npg_div', ['#3C5488', '#9FB0D8', '#F7F7F7', '#F3A08F', '#B5281A'])
