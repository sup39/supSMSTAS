# CHANGELOG
## \[v0.0.1.2] consider the -1 area of triangles (2022/07/20)
- WFC
  - consider the -1 area of triangles to improve the precision of WFC plot
- SMSDolphin
  - add `*args` and `**kwargs` to `hook()`
  - use sup-dolphin-memory-lib >= 0.1.2 to solve pid problem
## \[v0.0.1.1] improve performance by using PolyCollection (2022/07/19)
- WFC
  - improve process speed of `make_geo_plot()` by using PolyCollection
  - render dynamic triangle hitbox
- README
  - add Japanese version of README
## \[v0.0.1] init (2022/06/26)
- WFC
  - plot WFC hitbox (x-z plot and x/z-y plot) with matplotlib toolbar
  - options:
    - track Mario
    - show Mario as red point
    - airborne or grounded
    - on Yoshi
    - invert X/Z
  - angle dial for x/z-y plot
- Runtime
  - advance by QF
  - show Hitbox
