# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2022 sup39

def main():
  import os
  import sys
  import logging
  from .UI import MainWindow
  from PyQt5.QtWidgets import QApplication

  # set log level
  logging.basicConfig()
  def try_parse_int(x):
    try: return int(x)
    except: return None
  logLevelRaw = os.environ.get('LOG_LEVEL', 'WARNING')
  logLevel = try_parse_int(logLevelRaw)
  if logLevel is None: logLevel = try_parse_int(getattr(logging, logLevelRaw, None))
  ## logger
  logger = logging.getLogger('supSMSTAS')
  logger.setLevel(logging.WARNING if logLevel is None else logLevel)

  # execute
  app = QApplication(sys.argv)
  w = MainWindow()
  w.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
