# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2022 sup39

import numpy as np
from numpy import array
from .shape import Polyhedron
import matplotlib.patches as patches

class Surface:
  def __init__(self, surtype, surpara, trntype, unk7, verts, vidxs=None, n=None, c=None):
    self.surtype, self.surpara, self.trntype, self.unk7 = \
      surtype, surpara, trntype, unk7
    self.vidxs = vidxs
    self.verts = verts
    self.minY = verts[:,1].min()
    self.maxY = verts[:,1].max()
    self.n = normalize(np.cross(verts[1]-verts[0], verts[2]-verts[1])) if n is None else n
    self.c = -np.dot(verts[0], self.n) if c is None else c
  def __repr__(self):
    return 'minY=%.0f maxY=%.0f n=(%5.2f, %5.2f, %5.2f)'%(
      self.minY, self.maxY, *self.n,
    )

makeTriPrism = lambda tri0, tri1: Polyhedron([
  *tri0,
  *tri1,
], [
  (0, 1), (1, 2), (2, 0),
  (0, 3), (1, 4), (2, 5),
  (3, 4), (4, 5), (5, 3),
])

def makeGround(tri, hG=0):
  vertsLow = tri.verts-(0,108,0)
  ySlice = tri.minY-30
  v = array(vertsLow)
  vertsLow[:,1] = np.clip(vertsLow[:,1], a_min=ySlice, a_max=None)
  verts = [
    *vertsLow,
    *(tri.verts+(0,hG,0)),
  ]
  edges = [
    # top face
    (3, 4), (4, 5), (5, 3),
    # vertical edge
    (0, 3), (1, 4), (2, 5),
  ]
  r = v[:, 1]-ySlice
  b = r>0
  bc = b.sum()
  if bc in [0, 3]:
    # bottom face
    edges += [(0, 1), (1, 2), (2, 0)]
  else:
    k0 = np.where(b if bc==1 else ~b)[0][0]
    k1 = (k0+1)%3
    k2 = (k0+2)%3
    v0, r0 = v[k0], r[k0]
    v1, r1 = v[k1], r[k1]
    v2, r2 = v[k2], r[k2]
    verts += [
      (r1*v0-r0*v1)/(-r0+r1),
      (r2*v0-r0*v2)/(-r0+r2),
    ]
    edges += [
      (k0, 6), (6, k1),
      (k0, 7), (7, k2),
      (k1, k2), (6, 7),
    ]
  poly = Polyhedron(verts, edges)
  return poly
def makeRoof(tri, hR=82):
  poly = makeTriPrism(tri.verts-(0,hR,0), tri.verts-(0,160,0))
  return poly
def makeWall(tri, rW=50, dy=30):
  verts = tri.verts - (0, dy, 0)
  n = tri.n
  off = (np.abs(rW/n[0]),0,0) if np.abs(n[0])>0.707 else (0,0,np.abs(rW/n[2]))
  poly = makeTriPrism(verts-off, verts+off)
  return poly

def make_geo_plot(ax, hitboxs, p0, pn, axes):
  # paras
  arrowWidthBase = 60
  arrowWidthMul = 0.2
  arrowLenMax = 80
  arrowLenTher = 200
  arrowLenMul1 = 0.7
  arrowLenMul2 = 0.35
  arrowHeadLenMul = 0.3
  arrowLenMul2off = 0.025
  arrowCountMax = 20

  # plot
  for polys, awmul, alen, facecolor, arcolor in hitboxs:
    # draw wall hitboxs (draw in reverse order)
    for poly, n in polys[::-1]:
      # clip at y=yy and take (x, z) coordinate
      verts = poly.slicePlane(p0, pn)[:,axes]
      if len(verts) == 0: continue
      # plot hitbox area
      ax.add_patch(patches.Polygon(verts, fc=facecolor, ec='black', lw=1))
      # plot arrow
      n = n*(1, 0, 1) # no y arrow
      n = n[axes]
      nnorm = np.linalg.norm(n)
      if nnorm == 0: continue # TODO
      n = n/nnorm
      l = array([n[1], -n[0]])
      ## basis matrix
      B = np.vstack([n, l])
      ## center
      C = verts.mean(axis=0)
      vertsO = verts-C
      ## n-l coordinates
      nn = np.dot(vertsO, n)
      ll = np.dot(vertsO, l)
      ## determine arrow width and count
      iminl = ll.argmin()
      imaxl = ll.argmax()
      minl = ll[iminl]
      maxl = ll[imaxl]
      dl = maxl-minl
      arrowWidth = arrowWidthBase*awmul
      nArrow = np.floor(dl/arrowWidth).astype('i')
      if nArrow >= 1:
        if nArrow>arrowCountMax: nArrow = arrowCountMax
      else:
        arrowWidth = dl
        nArrow = 1
      arrowWidth *= arrowWidthMul
      ## determine arrow position
      vlen = len(verts)
      nbss = []
      ls = np.linspace(minl, maxl, nArrow+2)[1:-1]
      for step in [1, -1]:
        i0 = iminl
        i1 = (i0+step)%vlen
        nbs = []
        for lb in ls:
          while ll[i1] < lb: i0, i1 = i1, (i1+step)%vlen
          r0 = lb-ll[i0]
          r1 = ll[i1]-lb
          nbs.append((nn[i0]+nn[i1])/2 if r0+r1==0 else (nn[i0]*r1+nn[i1]*r0)/(r0+r1))
        nbss.append(nbs)
      nbss = array(nbss)
      ncts = nbss.mean(axis=0)
      nrgs = np.abs(np.diff(nbss, axis=0)[0])
      # add arrow
      for p, nrg in zip(
        C+np.matmul(np.column_stack([ncts, ls]), B),
        nrgs,
      ):
        if nrg > arrowLenTher:
          nrg = min(arrowLenMax, nrg*arrowLenMul2)
          dn = n * nrg
          offs = [-arrowLenMul2off, 1+arrowLenMul2off]
        else:
          nrg = min(arrowLenMax, nrg*arrowLenMul1)
          dn = n * nrg
          offs = [0.5]
        arrowHeadLen = nrg*arrowHeadLenMul
        for off in offs:
          ax.arrow(
            *(p-dn*off), *dn,
            width=arrowWidth, #min(arrowWidth, nrg*0.15),
            head_length=arrowHeadLen,
            length_includes_head=True,
            color=arcolor,
          )

  ax.set_xlabel('xyz'[axes[0]])
  ax.set_ylabel('xyz'[axes[1]])

  return axes
