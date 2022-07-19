# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2022 sup39

import numpy as np
from numpy import array
from .shape import Polyhedron
from matplotlib.collections import PolyCollection

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

def extendTriangle(tri, axis):
  ans = np.array(tri, 'd')
  tri = tri[:, axis]
  for i in [-1, 0, 1]:
    l1, l2 = tri[i]-tri[i+1], tri[i]-tri[i-1]
    ans[i, axis] += (l1+l2)/np.abs(np.cross(l1, l2).item())
  return ans

def makeGround(tri, hG=0):
  vertsE = extendTriangle(tri.verts, [0, 2])
  vertsLow = vertsE-(0,108,0)
  ySlice = tri.minY-30
  v = array(vertsLow)
  vertsLow[:,1] = np.clip(vertsLow[:,1], a_min=ySlice, a_max=None)
  verts = [
    *vertsLow,
    *(vertsE+(0,hG,0)),
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
  verts = extendTriangle(tri.verts, [0, 2])
  poly = makeTriPrism(verts-(0,hR,0), verts-(0,160,0))
  return poly
def makeWall(tri, rW=50, dy=30):
  n = tri.n
  isXWall = np.abs(n[0])>0.707
  verts = extendTriangle(tri.verts, [2 if isXWall else 0, 1]) - (0, dy, 0)
  off = (np.abs(rW/n[0]),0,0) if isXWall else (0,0,np.abs(rW/n[2]))
  poly = makeTriPrism(verts-off, verts+off)
  return poly

def make_geo_plot(ax, hitboxs, p0, pn, axes):
  # paras
  arrowWidthBase = 70
  arrowWidthMul = 0.5
  arrowLenMax = 200 #80
  arrowLenTher = 200
  arrowLenMul1 = 0.7
  arrowLenMul2 = 0.35
  arrowHeadLenMul = 0.3
  arrowLenMul2off = 0.1 #0.025
  arrowCountMax = 100
  aw, ah = 0.2, 0.6 # width, height of bottom rect
  arrowVerts = array([
    [0.0,  aw],
    [ ah,  aw],
    [ ah, 0.5],
    [1.0, 0.0],
    [ ah, -.5],
    [ ah, -aw],
    [0.0, -aw],
  ])

  # plot
  patches = []
  for polys, awmul, alen, facecolor, arcolor in hitboxs:
    # draw wall hitboxs (draw in reverse order)
    for poly, n in polys[::-1]:
      # clip at y=yy and take (x, z) coordinate
      verts = poly.slicePlane(p0, pn)[:,axes]
      if len(verts) == 0: continue
      # plot hitbox area
      patches.append((verts, facecolor, 'black')) # (verts, fc, ec)
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
      maty = array([-n[1], n[0]])*arrowWidth
      for p, nrg in zip(
        C+np.matmul(np.column_stack([ncts, ls]), B),
        nrgs,
      ):
        if nrg > arrowLenTher:
          nrg = min(arrowLenMax, nrg*arrowLenMul2)
          offs = [-arrowLenMul2off, 1+arrowLenMul2off]
        else:
          nrg = min(arrowLenMax, nrg*arrowLenMul1)
          offs = [0.5]
        dn = n * nrg
        # add patches
        verts0 = np.matmul(arrowVerts, [n*nrg, maty])
        for off in offs:
          patches.append((
            p-dn*off+verts0,
            arcolor, # fc
            arcolor, # ec
          ))

  if len(patches):
    ax.add_collection(PolyCollection(
      **{
        k: v
        for k, v in zip(('verts', 'facecolors', 'edgecolors'), zip(*patches))
      },
    ))

  ax.set_xlabel('xyz'[axes[0]])
  ax.set_ylabel('xyz'[axes[1]])

  return axes
