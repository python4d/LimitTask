#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
LimitTask module is a simple command to limit one specific windows processus (task) for a certain time during a slot of time (subscription).
LimitTask est un module python pour limiter l'usage d'un process windows dans le temps sur une plage de temps déterminé (abonnement).

Usage = 
          python.exe LimitTask.pyw <name_process/task.exe> <max use time> <abonnement/plage de temps>

@author: Python4D/damien.samain@python4d.com
@version: 0.1
@todo: minimum gui, password, create data in registery during reboot...
"""


import psutil
process = filter(lambda p: p.name == "LimitTask.exe", psutil.process_iter())


for i in process:
  i.kill()
    
