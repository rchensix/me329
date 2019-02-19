"""""
### xlattice visualize ###
Written by Lucas Zhou
Feb 17, 2019

This module generates .gif files for all lattices with a viewing angle sweeping from 15 degree to 75 degree.
"""""

import xlattice as xlt
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from xlattice import Lattice
from matplotlib import animation, rc
from IPython.display import HTML, Image
import math
import warnings
import sys

def animation_3d(G, title, frames_per_sec=15):
    fig = plt.figure(figsize=(8, 6))
    ax = Axes3D(fig)
    fig.suptitle(title, fontsize=20)
    if isinstance(G, Lattice):
        extents = G.extents
        G = G.G
    pos = nx.get_node_attributes(G, 'pos')
    with plt.style.context(('ggplot')):
        for key, value in pos.items():
            xi = value[0]
            yi = value[1]
            zi = value[2]
            ax.scatter(xi, yi, zi, s=20 + 20 * G.degree(key), edgecolors='k', alpha=0.7)
        for i, j in enumerate(G.edges()):
            x = np.array((pos[j[0]][0], pos[j[1]][0]))
            y = np.array((pos[j[0]][1], pos[j[1]][1]))
            z = np.array((pos[j[0]][2], pos[j[1]][2]))
            ax.plot(x, y, z, c='black', alpha=0.5)
    if extents != None:
            maxLength = max([extents[1] - extents[0], extents[3] - extents[2], extents[5] - extents[4]])
            ax.auto_scale_xyz([extents[0], extents[0] + maxLength], [extents[2], extents[2] + maxLength],
                              [extents[4], extents[4] + maxLength])

    def update(i):
        ax.view_init(30,i+15)
        return

    anim = animation.FuncAnimation(fig, update, frames=60, interval=150)
    outputfile = '../gifs/'+title+'.gif'
    anim.save(outputfile, writer='imagemagick', fps =frames_per_sec)

G_snap_2side = xlt.snapThroughLattice(30, 1, 0.1, (1, 1), both_side=True)
G_snap_2side_t = xlt.snapThroughLattice(30, 1, 0.1, (1, 1), both_side=True)
G_snap_2side_t.tessellate(2,2,2)

G_doubleSnap_2side = xlt.doubleSnapThroughLattice(35,15,1,0.1,(1,1), True)
G_doubleSnap_2side_t = xlt.doubleSnapThroughLattice(35,15,1,0.1,(1,1), True)
G_doubleSnap_2side_t.tessellate(2,2,2)

G_sc = xlt.simpleCubicLattice(1,1,1)
G_sc_t = xlt.simpleCubicLattice(1,1,1)
G_sc_t.tessellate(2,2,2)

G_bcc = xlt.bccLatice(1,1,1)
G_bcc_t = xlt.bccLatice(1,1,1)
G_bcc_t.tessellate(2,2,2)

G_fcc = xlt.fccLattice(1,1,1)
G_fcc_t = xlt.fccLattice(1,1,1)
G_fcc_t.tessellate(2,2,2)

G_fcc_open = xlt.fccLattice(1,1,1, True)
G_fcc_open_t = xlt.fccLattice(1,1,1, True)
G_fcc_open_t.tessellate(2,2,2)

G_hex = xlt.regularHexagonLattice(1,1)
G_hex_t = xlt.regularHexagonLattice(1,1)
G_hex_t.tessellate(2,3,4)

G_diamond = xlt.diamondLattice(1,1,1)
G_diamond_t = xlt.diamondLattice(1,1,1)
G_diamond_t.tessellate(4, 4, 4)

G_tri = xlt.regularTriangleLattice(1, 0.1)
G_tri_t = xlt.regularTriangleLattice(1, 0.1)
G_tri_t.tessellate(2,4,2)

lattice_dict = {
                G_snap_2side:'Snap-through_Lattice', G_snap_2side_t:'Snap-through_Lattice 2X2X2',
                G_doubleSnap_2side:'Double_Snap-through_Lattice', G_doubleSnap_2side_t:'Double_Snap-through_Lattice 2X2X2',
                G_sc:'Simaple Cubic', G_sc_t:'Simaple Cubic 2X2X2',
                G_bcc:'BCC', G_bcc_t:'BCC 2X2X2',
                G_fcc: 'FCC Closed-type', G_fcc_t:'FCC Closed-type 2X2X2',
                G_fcc_open: 'FCC Open-type', G_fcc_open_t:'FCC Open-type 2X2X2',
                G_hex:'Regular Hexagon Lattice', G_hex_t: 'Regular Hexagon Tessellation 2X3X4 (Honeycomb)',
                G_diamond: 'Diamond Lattice', G_diamond_t:'Diamond Lattice 4X4X4',
                G_tri: 'Regular Triangle Lattice', G_tri_t: 'Regular Triangle Lattice 2X4X2'
                }
for each in lattice_dict:
    animation_3d(each, lattice_dict[each])

