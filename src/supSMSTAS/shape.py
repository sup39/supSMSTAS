# SPDX-License-Identifier: MIT
# Copyright (c) 2022 sup39[サポミク]

import numpy as np
array = np.array
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib import patches
def normalize(x):
  l = np.linalg.norm(x)
  return x if l==0 else x/l

# 多角形
class Polygon():
  def __init__(self, verts):
    '''
    * self.verts:
      頂点の配列
      Array of vertices
    '''
    self.verts = np.array(verts)
  def clipLine(self, p, n, c):
    '''
    半平面 (x-p)・n >= c との共通部分を取る
    Take intersection with half plane (x-p)・n >= c
    * p:
      直線上の一点
      Any point on the line
    * n:
      直線の法線ベクトル
      Normal vector of the line
    * c:
      定数
      Constant
    '''
    p, n, c = map(array, (p, n, c))
    r = np.dot(self.verts-p, n)-c
    verts = []
    for i in range(len(r)):
      v0, r0 = self.verts[i-1], r[i-1]
      v1, r1 = self.verts[i], r[i]
      if r1 >= 0:
        if r0 < 0: # (- +)
          verts.append((r1*v0-r0*v1)/(-r0+r1))
        verts.append(v1)
      elif r0 >= 0: # (+ -)
        verts.append((-r1*v0+r0*v1)/(r0-r1))
    self.verts = np.array(verts) if len(verts) else self.verts[:0]
  @property # getter
  def path(self):
    if self.verts.shape[0] == 0: return None
    verts = self.verts
    assert verts.shape[-1] == 2, 'verts should be 2D'
    return Path([*verts, (0, 0)], [
      Path.MOVETO,
      *(Path.LINETO for _ in range(1, verts.shape[0])),
      Path.CLOSEPOLY,
    ])
  def plot(self, margin=0.05, facecolor='#2ee5b8', lw=1):
    '''
    この多角形を描画し、figとaxを返す
    Plot this polygon and return ``fig'' and ``ax''
    * margin:
      Set margin of the plot
    * facecolor:
      面の色
      Face color
    * lw:
      線の太さ
      Line width
    '''
    fig, ax = plt.subplots()
    if self.verts.shape[0] == 0: return ax
    # path
    path = self.path
    patch = patches.PathPatch(path, facecolor=facecolor, lw=lw)
    ax.add_patch(patch)
    verts = self.verts
    xMax, yMax = verts.max(axis=0)
    xMin, yMin = verts.min(axis=0)
    xMg, yMg = verts.ptp(axis=0)*margin
    ax.set_xlim(xMin-xMg, xMax+xMg)
    ax.set_ylim(yMin-yMg, yMax+yMg)
    return fig, ax
  def __repr__(self):
    return 'Polygon with %d vertices:\n%s'%(
      len(self.verts),
      array(self.verts, 'f'),
    )

# 多面体
class Polyhedron:
  def __init__(self, verts, edges):
    '''
    * self.verts:
      頂点の配列
      Array of vertices
    * self.edges:
      辺(2頂点の番号)の配列
      Array of edges (indices of 2 vertices)
    '''
    self.verts = np.array(verts)
    self.edges = np.array(edges)
  def clipPlane(self, p, n, c=0):
    '''
    半空間 (x-p)・n >= c との共通部分を取る
    Take intersection with half space (x-p)・n >= c
    * p:
      平面上の一点
      Any point on the plane
    * n:
      直線の法線ベクトル
      Normal vector of the plane
    * c:
      定数
      Constant
    '''
    p = array(p)
    n = array(n)
    r = np.dot(self.verts-p, n)-c
    rb = [s>=0 for s in r]
    # map vertex indices old to new
    io2n = {
      iO: iN
      for iN, iO in enumerate(iO for iO, sb in enumerate(rb) if sb)
    }
    # handle old vert
    verts = [v for v, sb in zip(self.verts, rb) if sb]
    edges = []
    for i0, i1 in self.edges:
      if rb[i0] and rb[i1]:
        # remain
        edges.append((io2n[i0], io2n[i1]))
      elif rb[i0] or rb[i1]:
        # new vert
        v0, r0 = self.verts[i0], abs(r[i0])
        v1, r1 = self.verts[i1], abs(r[i1])
        vN = (r1*v0+r0*v1)/(r0+r1)
        edges.append((io2n[i0 if rb[i0] else i1], len(verts)))
        verts.append(vN)
      # else drop edge
    # add new face
    nOld = len(io2n)
    vNews = verts[nOld:]
    if len(vNews):
      assert len(vNews) >= 3
      p0, p1 = vNews[:2]
      # choose p1-p0 as e1
      e1 = normalize(p1-p0)
      # choose e2 that ⊥ n, e1
      e2 = normalize(np.cross(n, e1))
      # set (p0+p1)/2 as new origin, and use {e1, e2} as new basis
      cNews = np.dot(vNews-(p0+p1)/2, array([e1, e2]).transpose())
      # indices of new verts CCW
      jNews = nOld+np.arctan2(cNews[:,0], cNews[:,1]).argsort()
      # add to edge
      for i in range(len(vNews)):
        edges.append((jNews[i-1], jNews[i]))
    # final
    self.verts = array(verts)
    self.edges = array(edges)
  def slicePlane(self, p, n):
    '''
    平面 (x-p)･n=0 との共通部分(多角形)の頂点を返す
    Return vertices of intersection(polygon) with plane (x-p)･n=0
    * p:
      平面上の一点
      Any point on the plane
    * n:
      平面の法線ベクトル
      Normal vector of the plane
    '''
    p = array(p)
    n = array(n)
    r = np.dot(self.verts-p, n)
    # handle old verts
    #for i0, i1 in self.edges:
    #  # two vertices on other side of the plane
    #  if np.sign(r[i0]) != np.sign(r[i1]):
    #    v0, r0 = self.verts[i0], abs(r[i0])
    #    v1, r1 = self.verts[i1], abs(r[i1])
    #    vN = (r1*v0+r0*v1)/(r0+r1)
    #    vNews.append(vN)
    signr = np.sign(r[self.edges])
    edgesNew = self.edges[signr[:,0]!=signr[:,1]]
    vv = self.verts[edgesNew]
    rr = np.abs(r[edgesNew])
    vNews = ((vv[:,0]*rr[:,1,None])+(vv[:,1]*rr[:,0,None]))/rr.sum(axis=1)[:,None]
    # new verts
    if len(vNews):
      assert len(vNews) >= 2
      p0, p1 = vNews[:2]
      e1 = normalize(p1-p0)
      e2 = normalize(np.cross(n, e1))
      cNews = np.dot(vNews-(p0+p1)/2, array([e1, e2]).transpose())
      jNews = np.arctan2(cNews[:,0], cNews[:,1]).argsort()
      return vNews[jNews]
    else:
      return vNews
  def __repr__(self):
    return 'Polyhedron with %d vertices and %d edges:\n%s'%(
      len(self.verts), len(self.edges),
      array(self.verts[self.edges], 'f')
    )
