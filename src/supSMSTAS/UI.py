# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2022 sup39

import os
import time
## numpy
import numpy as np
from numpy import array
## matplotlib
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.patches as patches
## PyQt5
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
## logging
import logging
## local
from .WFC import *

# add TRACE
logging.TRACE = 5
logging.addLevelName(logging.TRACE, 'TRACE')
def trace(self, message, *args, **kws):
  if self.isEnabledFor(logging.TRACE):
    self._log(logging.TRACE, message, args, **kws)
logging.Logger.trace = trace
# logger
logger = logging.getLogger('supSMSTAS')

# widgets utils
def layoutAddItem(ll, w):
  if w is None: ll.addStretch()
  elif isinstance(w, QLayout): ll.addLayout(w)
  else: ll.addWidget(w)
def HBox(*children, **kwargs):
  ll = QHBoxLayout(**kwargs)
  for w in children: layoutAddItem(ll, w)
  return ll
def VBox(*children, **kwargs):
  ll = QVBoxLayout(**kwargs)
  for w in children: layoutAddItem(ll, w)
  return ll

class MPLCanvas(FigureCanvasQTAgg):
  def __init__(self, parent=None, width=5, height=5, dpi=100):
    fig = self.fig = Figure(figsize=(width, height), dpi=dpi)
    self.axs = [
      fig.add_subplot(121),
      fig.add_subplot(122),
    ]
    super().__init__(fig)

# Dolphin for SMS
from dolphin.memorylib import Dolphin
class SMSDolphin(Dolphin):
  symbols = { # TODO
    b'GMSJ01\x00\x00': {
      'gpMarioOriginal': 0x8040A378,
      'gpMap': 0x8040A570,
    }
  }
  def get_symb_addr(self, name): # override
    verID = self.memory.buf[:8].tobytes()
    return SMSDolphin.symbols[verID][name]

  def __init__(self):
    super().__init__()
    self.hooked = False
  def hook(self):
    self.hooked = False
    if Dolphin.hook(self) is None:
      return 'SMS is not running'
    # found pid -> check game
    verID = self.memory.buf[:8].tobytes()
    if verID[:3] != b'GMS':
      return 'Current game is not SMS'
    if verID not in SMSDolphin.symbols:
      return 'Only NTSJ-1.0 is supported in this version'
    self.hooked = True

  def checkList2list(self, ptr):
    ans = []
    while ptr:
      ptr, data = self.read_struct(ptr+4, '>II')
      ans.append(Surface(
        *self.read_struct(data, '>HHBB'),
        array(self.read_struct(data+0x10, '>9f'), 'f').reshape(3, 3),
        n=array(self.read_struct(data+0x34, '>3f'), 'f'),
        c=self.read_float(data+0x40),
      ))
    return ans

# widgets
class WFCWidget(QWidget):
  def __init__(self, dolphin, parent=None):
    super().__init__(parent=parent)
    self.d = dolphin
    self._init_state()
    self._init_layout()
  def activate(self, val):
    # stop timer if deactivate
    self.setFPS(self.fps) if val else self.timer.stop()
  def _init_state(self):
    self.trackMario = Qt.Checked
    self.showMario = Qt.Checked
    self.airborne = Qt.Checked
    self.yoshi = 0
    self.fps = 4
    self.updating = False
    self.invertX = 0
    self.invertZ = 0
    self.xzAngle = 0
  def _init_layout(self):
    # timer
    timer = self.timer = QTimer()
    timer.timeout.connect(self.updatePlot)
    # mcv
    self.mcv = mcv = MPLCanvas(self, width=11, height=5, dpi=100)
    self.updatePlot()
    # toolbar
    toolbar = NavigationToolbar2QT(mcv, self)
    # buttons
    llbtn = QHBoxLayout()
    btn = QPushButton()
    btn.setText('Update plot')
    btn.clicked.connect(self.updatePlot)
    llbtn.addWidget(btn)
    # update
    lbFPS = QLabel()
    lbFPS.setText('fps')
    sbFPS = QSpinBox()
    sbFPS.setRange(0, 60)
    sbFPS.setValue(self.fps)
    #cbFPS.setText('fps')
    sbFPS.valueChanged.connect(lambda: self.setFPS(sbFPS.value()))
    self.setFPS(self.fps)
    ## add widget
    llbtn.addWidget(lbFPS)
    llbtn.addWidget(sbFPS)
    for text, attr in [
      ('Track Mario', 'trackMario'),
      ('Show Mario', 'showMario'),
      ('Airborne', 'airborne'),
      ('Yoshi', 'yoshi'),
      ('invert X', 'invertX'),
      ('invert Z', 'invertZ'),
    ]:
      cb = QCheckBox()
      cb.setText(text)
      cb.setCheckState(getattr(self, attr))
      cb.clicked.connect((lambda attr, cb: lambda: setattr(self, attr, cb.checkState()))(attr, cb))
      llbtn.addWidget(cb)
    llbtn.addStretch()
    # angle
    lbXZAngle = QLabel()
    lbXZAngle.setText('Angle')
    dlXZAngle = QDial()
    dlXZAngle.setWrapping(True)
    #dlXZAngle.setNotchesVisible(True) # TODO
    dlXZAngle.valueChanged.connect(lambda: self.setXZAngle(dlXZAngle.value()))
    ## angle button
    llXZAngleBtns = QVBoxLayout()
    for text, val in [
      ('X+', 75),
      ('X-', 25),
      ('Z+', 50),
      ('Z-', 0),
    ]:
      btn = QPushButton()
      btn.setText(text)
      btn.clicked.connect((lambda val: lambda: dlXZAngle.setValue(val))(val))
      llXZAngleBtns.addWidget(btn)
    # footer
    llFooter = HBox(
      # buttons
      VBox(
        llbtn,
        None,
      ),
      None,
      ## angle
      lbXZAngle,
      dlXZAngle,
      llXZAngleBtns,
    )
    # layout
    self.setLayout(VBox(
      toolbar,
      mcv,
      llFooter,
    ))
  def toggleTimer(self, toggle):
    if toggle:
      self.timer.start()
    else:
      self.timer.stop()
  def setFPS(self, fps):
    self.fps = fps
    if fps == 0:
      self.timer.stop()
    else:
      self.timer.setInterval(int(1000/fps))
      self.timer.start()
  def setXZAngle(self, val):
    self.xzAngle = val
    #self.updatePlot()
  def updatePlot(self):
    if self.updating or not self.d.hooked: return
    self.updating = True
    try: self._updatePlot()
    except:
      import traceback
      traceback.print_exc()
    self.updating = False
  def _updatePlot(self):
    d = self.d
    pos = d.read_struct(('gpMarioOriginal', 0x10), '>3f')
    if pos is None: return
    pos = array(pos)
    x, y, z = pos
    # get collision data (static collision)
    colInfo = d.read_struct(('gpMap', 0x10, 0), '>ffI4x4xI')
    if colInfo is None: return
    xLimit, zLimit, xBlockCount, ptrStCLR = colInfo
    ## TBGCheckListRoot[zBlockCount][xBlockCount]
    colOff = int((z+zLimit)//1024*xBlockCount + (x+xLimit)//1024)*36
    ## root->ground(12*2).next(4)

    # mario
    yoshi = self.yoshi
    airborne = self.airborne
    rW = 80 if yoshi else 50

    t0 = time.time()
    stGnds, stRoofs, stWalls = [
    #data1 = [ # TODO dynamic data
      d.checkList2list(d.read_uint32(ptrStCLR+colOff+4+12*j))
      for j in range(3)
    ]
    hitboxs = [
      # ceiling
      ([
        #(c, array((0, -1, 0)))
        (makeRoof(tri, 82 if airborne else 2), array([0, -1, 0]))
        for tri in stRoofs
        #for c in makeCol(tri, airborne=airborne, yoshi=yoshi)
      # if tri.maxY >= yMin
      ##], 1.0, 78.0 if airborne else 158.0, '#f88e', '#800'),
      ## FIXME: draw arrow
      ], 1.0, 0, '#f88e', '#800'),
      ([
        #(c, array((0, 1, 0)))
        (makeGround(tri, 0 if airborne else 0), array([0, 1, 0])) # TODO hG=100
        for tri in stGnds # TODO grounded hitbox
        #for c in makeCol(tri, airborne=airborne, yoshi=yoshi)
      # if tri.maxY >= yMin
      ## FIXME: draw arrow
      ], 1.0, 0, '#88fe', '#008'), # TODO
      *(
        ([
          #(c, tri.n)
          (makeWall(tri, w, dy), tri.n)
          for tri in stWalls
          #for c in [makeCol(tri, airborne=airborne, yoshi=yoshi)[ii]]
        # if tri.maxY >= yMin
        # arrow size scale (0.5 if radius is 25)
        ], 1.0 if airborne or ii == 1 else 0.5, rW, ['#8fcc', '#8f8c'][ii], ['#084', '#080'][ii])
        #], 1.0 if airborne or ii == 1 else 0.5, rW, '#8f8e', '#080')
        for ii, (w, dy) in zip((1, 0), [(rW, 30), (rW, 150)] if airborne else [(rW, 60), (rW/2, 30)])
      ),
    ]
    # xzAngle
    theta = self.xzAngle/50*np.pi
    pnXZ = (-np.sin(theta), 0, -np.cos(theta))
    axesXZ = [2 if abs(pnXZ[0])>abs(pnXZ[2]) else 0, 1]
    invertX = self.invertX==Qt.Checked
    invertZ = self.invertZ==Qt.Checked
    # ax
    xzAngle = self.xzAngle
    for ax, (pn, axes) in zip(self.mcv.axs, [
      ((0, 1, 0), [0, 2]),
      (pnXZ, axesXZ),
    ]):
      ax.patches.clear()
      make_geo_plot(ax, hitboxs, pos, pn, axes)
      if self.showMario:
        ax.add_patch(patches.Circle(pos[axes], 25, fc='red'))
      if self.trackMario:
        offs = [(-1000, 1000), (-1000, 1000), (-1000, 1000)] # TODO
        for f, i in zip((ax.set_xlim, ax.set_ylim), axes):
          p = pos[i]
          d0, d1 = offs[i]
          if invertX & (i==0) | invertZ & (i==2): # invert
            d0, d1 = d1, d0
          f(p+d0, p+d1)
      ax.grid(True)
    # apply
    self.mcv.fig.tight_layout()
    self.mcv.draw()
    logger.trace('%.2f'%((time.time()-t0)*1000))

class RuntimeWidget(QWidget):
  def __init__(self, dolphin, parent=None):
    super().__init__(parent=parent)
    self.d = dolphin
    self._init_state()
    self._init_layout()
  def _init_state(self):
    pass
  def _init_layout(self):
    # QF
    cbQF = QCheckBox()
    cbQF.setText('Advance by QF')
    cbQF.clicked.connect(lambda: self.toggleQFSync(cbQF.checkState()))
    # hitbox
    cbHitbox = QCheckBox()
    cbHitbox.setText('Show hitbox')
    cbHitbox.clicked.connect(lambda: self.toggleHitbox(cbHitbox.checkState()))
    # layout
    self.setLayout(VBox(
      cbQF,
      cbHitbox,
      None,
    ))
  def toggleQFSync(self, val):
    self.d.write_uint8(0x817F1000, 1 if val else 0)
  def toggleHitbox(self, val):
    ptrAddr = 0x817F1010
    funcAddr = 0x817E05B8 # TODO
    baseAddr = 0x817E0000
    if val: # TODO other scripts
      baseDir = os.path.dirname(__file__)
      with open(os.path.join(baseDir, 'codes/showHitbox.bin'), 'rb') as fr:
        buf = fr.read()
      self.d.memory.buf[baseAddr-0x80000000:baseAddr-0x80000000+len(buf)] = buf
      self.d.write_uint32(ptrAddr, funcAddr)
    else:
      self.d.write_uint32(ptrAddr, 0)

class MainWindow(QMainWindow):
  def __init__(self, dolphin=None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.setWindowTitle("supSMSTAS")
    self.dolphin = SMSDolphin() if dolphin is None else dolphin
    self._init_layout()
    self.hook()
  def _init_layout(self):
    # hook button bar: btHook, lbHook, (spacer)
    btHook = QPushButton()
    btHook.setText('Hook')
    btHook.clicked.connect(self.hook)
    self.lbHook = lbHook = QLabel()
    lbHook.setText('')
    llHook = HBox(
      btHook,
      lbHook,
      None,
    )
    ## tab
    qtab = self.qtab = QTabWidget(self)
    self.subwWFC = WFCWidget(dolphin=self.dolphin)
    self.tidxWFC = qtab.addTab(self.subwWFC, 'WFC')
    self.subwRuntime = RuntimeWidget(dolphin=self.dolphin)
    self.tidxRuntime = qtab.addTab(self.subwRuntime, 'Runtime')
    qtab.currentChanged.connect(lambda: self.onTabChanged(qtab.currentIndex()))
    # dummy widget to put widgets in the center
    w = QWidget()
    w.setLayout(VBox(
      llHook,
      qtab,
      None,
    ))
    self.setCentralWidget(w)
  def hook(self):
    err = self.dolphin.hook()
    self.lbHook.setText('Hooked' if err is None else err)
    self.qtab.setEnabled(self.dolphin.hooked)
  def onTabChanged(self, index):
    self.subwWFC.activate(index==self.tidxWFC)
