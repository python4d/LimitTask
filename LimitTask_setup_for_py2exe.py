#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
LimitTask_set_for_py2exe module create a windows executable of LimitTask.pyw
(use LimitTask.pyw instead of LimitTask.py to avoid/hide console)

Usage = python.exe LimitTask.py <nom_du_process.exe> <tps max d'utilisation> <abonnement/plage de temps>

@author: Python4D/damien.samain@python4d.com
@version: 0.1
@todo: minimum 
"""

from distutils.core import setup
import py2exe

setup(
      options = {"py2exe": {
                              "compressed": 1,
                              "bundle_files": 3,
                              #'dll_excludes': [ "mswsock.dll", "powrprof.dll" ] #need it (cf http://stackoverflow.com/questions/2104611/memoryloaderror-when-trying-to-run-py2exe-application)
                             } },
      console=['LimitTask.py'] #pour cacher la 'console' mettre 'windows'
       
      )