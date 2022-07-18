# supSMSTAS
<p align="center">
  <span>English</span> |
  <a href="https://github.com/sup39/supSMSTAS/blob/main/README.ja.md">日本語</a>
</p>

*A tool to **sup**port **S**uper **M**ario **S**unshine **T**ool **A**ssisted **S**peedrun/Superplay*

## Installation/Update
```
pip install -U supSMSTAS
```
:warning: Python 3.8 or above is required

## Usage
```
python -m supSMSTAS
```

## Required Gecko code
You need to add and activate the following Gecko code in Dolphin:
```
C20ECDE0 00000004
3C60817F 80631000
7C631B79 38600258
41820008 38600096
60000000 00000000
C20ED284 00000005
4E800021 3D60817F
816B1010 55608380
2800817E 4082000C
7D6803A6 4E800021
60000000 00000000
```

Make sure to disable those codes that
alter QF sync (advance by QF) or render triangle/hitbox
if you are using any of them.

If the checkboxes in the Runtime tab don't work,
try to disable all Gecko codes in Dolphin (except the *required Gecko code* mentioned above).

## Execute the source code directly
To install dependencies, the easiest way is to run the following command
in the root directory of the package:
```
pip install .
```

Due to some module/script problems,
in order to start the program,
instead of using `python path/to/supSMSTAS/__main__.py` (as script),
make sure to use `python -m path.to.supSMSTAS` (as module) outside the `src/supSMSTAS/` directory.
For example, if you are in the `src/` directory, you can run the following command:
```
python -m supSMSTAS
```
