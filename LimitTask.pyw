#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
LimitTask module is a simple command to limit one specific windows processus (task) for a certain time during a slot of time (subscription).
LimitTask est un module python pour limiter l'usage d'un process windows dans le temps sur une plage de temps d�termin� (abonnement).

Usage = 
          python.exe LimitTask.pyw <name_process/task.exe> <max use time> <abonnement/plage de temps>

@author: Python4D/damien.samain@python4d.com
@version: 0.1
@todo: minimum gui, password, create data in registery during reboot...
"""

import wmi,time,sys,os
import threading
import logging
import pythoncom
import win32gui


class LimitTask(object):
  def __init__(self, *args, **kwargs):
    self.c=wmi.WMI( *args, **kwargs)
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='LimitTask.log',
                    filemode='w+')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
        
  def WaitOutTask(self,TaskId):
    pythoncom.CoInitialize()
    try:
      c = wmi.WMI ()
      WatchDeletion = c.watch_for (notification_type="Deletion", wmi_class="Win32_Process", delay_secs=1, ProcessId=TaskId) 
      wd=WatchDeletion()
      self.flag=1
    finally:
      pythoncom.CoUninitialize()

  def KillTask(self,Task,NbMin=60,Plage=60*24):
    TaskTime=0  
    PlageTime=time.time()
    LastTaskTime=0
    state=10
    if NbMin>=Plage : 
      win32gui.MessageBox(0, "Attention la Plage de remise à zéro doit être Supérieure au temps de la tache/jeu!", "Erreur de lancement !",4096)
      return 1
    #TODO: pas vraiment optimisé, il faudrait reprendre la state machine pour incorporé les deux boucles while en une seule "while true"
    #TODO: on a séparé la state machine qui controle le temps de tache avec celle de la plage 
    WatchCreation=self.c.watch_for(notification_type="Creation", wmi_class="Win32_Process",delay_secs=1,name=Task)
    while True: #Boucle infinie gérant la vérification de la plage et tasktime
      print "WHILE TRUE => state={:d}, tasktime={:4.1f}, plagetime={:4.1f}".format(state,TaskTime,time.time()-PlageTime)
      while TaskTime<NbMin*60: #boucle (statemachine) gérant le temps d'entrée et sortie dans la tache
        print "WHILE TaskTime<NbMin*60 => state={:d}, tasktime={:4.1f}, plagetime={:4.1f}".format(state,TaskTime,time.time()-PlageTime)
        if state==10: # init des flags et Temps
          self.flag=0 #flag de la tache dThread pour vérifier si on est sortie de la tache
          self.flag_message=0
          TaskTime=0  
          PlageTime=time.time()
          LastTaskTime=0
          state=20
        elif state==20:
          process=[]
          process=self.c.Win32_Process(name=Task)
          if process==[]:
            state=40
          else:
            print "task trouvé! Id={:d} -Name={}\n".format(process[0].ProcessId,process[0].Name)
            _ProcessId=process[0].ProcessId
            state=50
        elif state==40:
          wc=WatchCreation() #ne sort pas de cette ligne tant qu'il n'y pas de création de la task
          if PlageTime+Plage*60<time.time():
            print "Remise à zéro au début Task !\n"            
            state=10 #On reset tout
          else:
            print "In:%f\n" % TaskTime
            state=20 #on revérifie que le task est bien présent
        elif state==50:#task présent reprise du calcul du temps
          start=time.time()
          t=threading.Thread(target=self.WaitOutTask,args=(_ProcessId,))
          t.start()
          state=60
        elif state==60:
          if self.flag==1:     #Est-on sorti de la tache flag positionné par le Thread?
            self.flag=0
            logging.info(u"Sortie de {} - Temps total de jeu = {:4.1f} minutes- Temps avant remise à zéro ={:4.1f} minute(s)!".format(Task,TaskTime/60.0,(Plage*60+PlageTime-time.time())/60.0)) 
            print"Out:%f\n" % TaskTime
            LastTaskTime=TaskTime #récupération du temps déjà écoulé
            state=20 #on retourne vérifier qu'il n'y a plus de process en cours
          else:
            time.sleep(1)
            TaskTime=LastTaskTime+time.time()-start
            if PlageTime+Plage*60<time.time():
              print "Remise à zéro avant la fin de TaskTime !\n"
              state=10 #On reset tout
#fin de While TaskTime<NbMin*60 => le temps limite et dépassé
      time.sleep(1)      
      process=self.c.Win32_Process(name=Task)
      if process==[]: #pas de process en cours
        if PlageTime+Plage*60<time.time():
          print "Remise à zéro en dehors du jeu!\n"
          TaskTime=0  #permet de rerentrer dans la state machine 
          state=10
      else:
        if not self.flag_message==2:
          win32gui.MessageBox(0, "Tu dois quitter le jeu maintenant - Tu as dépassé les {:4.1f} minute(s) !".format(NbMin), "QUOTA DEPASSE !",4096)
          result = process[0].Terminate ()
          self.flag_message=2
        else:
          result = process[0].Terminate ()
          logging.info("!Tentative d'entrée dans "+Task+" - Temps restant à attendre ={:4.1f} minute(s)!".format(NbMin,(Plage*60+PlageTime-time.time())/60.0))  
          win32gui.MessageBox(0, "Tu as dépassé tes {:4.0f} minute(s) de jeu,\n tu dois attendre encore {:4.1f} minute(s) pour rejouer !".format(NbMin,(Plage*60+PlageTime-time.time())/60.0), "QUOTA DEPASSE !", 4096)          


  
if __name__=="__main__":
  if len(sys.argv)!=4:
    win32gui.MessageBox(0,
u"""Attention ! il y 3 arguments à cette commande:

        1) 'nom de la tache' task présente dans la liste des processus windows
        2) tps de jeu (minutes)
        3) tps remise à zéro (minutes)
        
    Exemple (pour limiter la l'utilisation de la calculatrice à 10 mn toutes les 60mn):
    
               >>{} calc.exe 10 60""".format(sys.argv[0].split(os.path.sep)[-1:][0][:-4]), "Erreur de lancement !",4096) #récupération du dernier élément du fullpath [-1:] d'une liste [0], sans les 4 derniers caractères
  else:
    #TODO: vérifier qu'un autre LimitTask.exe n'existe pas avec la même tache
    MyPC=LimitTask()
    MyPC.KillTask(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
    
