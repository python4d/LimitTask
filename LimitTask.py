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

import time,sys,os
import threading
import logging
import win32gui,win32console
import psutil
import subprocess
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008
debug=0

class LimitTask(object):
  def __init__(self):
    self.WatcherPID=-1
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='LimitTask.log',
                    filemode='w+')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

  def KillTask(self,Task,NbMin=60,Plage=60*24):
    TaskTime=0  
    PlageTime=time.time()
    LastTaskTime=0
    state=10
    if NbMin>=Plage : 
      win32gui.MessageBox(0, "Attention la Plage de remise Ã  zÃ©ro doit Ãªtre SupÃ©rieure au temps de la tache/jeu!", "Erreur de lancement !",4096)
      return 1
    #TODO: pas vraiment optimisé, il faudrait reprendre la state machine pour incorporé les deux boucles while en une seule "while true"
    #TODO: on a séparé la state machine qui controle le temps de tache avec celle de la plage 
    while True: #Boucle infinie gÃ©rant la vÃ©rification de la plage et tasktime
      print "WHILE TRUE => state={:d}, tasktime={:4.1f}, plagetime={:4.1f}".format(state,TaskTime,time.time()-PlageTime)
      while TaskTime<NbMin*60: #boucle (statemachine) gÃ©rant le temps d'entrÃ©e et sortie dans la tache
        print "WHILE TaskTime<NbMin*60 => state={:d}, tasktime={:4.1f}, plagetime={:4.1f}".format(state,TaskTime,time.time()-PlageTime)
        if state==10: # init des flags et Temps
          self.flag_message=0
          TaskTime=0  
          PlageTime=time.time()
          LastTaskTime=0
          state=20
        elif state==20:
          searchPID=int(self.FindPID(Task)[1])
          if searchPID!=-1:
            if PlageTime+Plage*60<time.time():
              print "Remise à zéro au début Task !\n"            
              state=10 #On reset tout
            else:
              state=50
          else:
            time.sleep(1)
            state=20
        elif state==50:#task présent reprise du calcul du temps
          print "task trouvé! Id={:d}\n".format(searchPID)
          _ProcessId=searchPID
          print "In:%f\n" % TaskTime
          depart=time.time()
          state=60
        elif state==60:
          if not psutil.pid_exists(_ProcessId):
            logging.info(u"Sortie de {} - Temps total de jeu = {:4.1f} minutes- Temps avant remise à zéro ={:4.1f} minute(s)!".format(Task,TaskTime/60.0,(Plage*60+PlageTime-time.time())/60.0)) 
            print"Out:%f\n" % TaskTime
            LastTaskTime=TaskTime #récupération du temps déjà  écoulé
            state=20 #on retourne vérifier qu'il n'y a plus de process en cours
          else:
            time.sleep(1)
            TaskTime=LastTaskTime+time.time()-depart
            if PlageTime+Plage*60<time.time():
              print "Remise à zéro avant la fin de TaskTime !\n"
              state=10 #On reset tout
#fin de While TaskTime<NbMin*60 => le temps limite et dépassé
      time.sleep(1)      
      process = filter(lambda p: p.name == Task, psutil.process_iter())
      if process==[]: #pas de process Task en cours
        if PlageTime+Plage*60<time.time():
          print "Remise à zéro en dehors du jeu!\n"
          TaskTime=0  #permet de rerentrer dans la state machine 
          state=10
      else:
        if not self.flag_message==2:
          win32gui.MessageBox(0, "Tu dois quitter le jeu maintenant - Tu as dépassé les {:4.1f} minute(s) !".format(NbMin), "QUOTA DEPASSE !",4096)
          result = process[0].kill()
          self.flag_message=2
        else:
          result = process[0].kill()
          logging.info("!Tentative d'entrée dans "+Task+" - Temps restant à attendre ={:4.1f} minute(s)!".format(NbMin,(Plage*60+PlageTime-time.time())/60.0))  
          win32gui.MessageBox(0, "Tu as dépassé tes {:4.0f} minute(s) de jeu,\n tu dois attendre encore {:4.1f} minute(s) pour rejouer !".format(NbMin,(Plage*60+PlageTime-time.time())/60.0), "QUOTA DEPASSE !", 4096)   
                 
  def CreateTheWatcher(self,argv):
    path = '.\\dist\\' if debug==1 else ''
    print "CreateTheWatcher: START ! {} =".format(self.WatcherPID)
    if not psutil.pid_exists(self.WatcherPID): #il n'existe pas de Watcher on va le créer 
      LimitTask_name=path+argv[0].split(os.path.sep)[-1:][0].split(".")[0]+".exe"
      command=[LimitTask_name,argv[1],argv[2],argv[3],"-LimitTask"+str(os.getpid())]
      try:
        _r=subprocess.Popen(command,creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(0.5)
        #_r=self.FindPID(LimitTask_name.split(os.path.sep)[-1:][0])
        self.WatcherPID=int(_r.pid)
        
        threading.Timer(1,self.CreateTheWatcher,[argv,]).start() #on relance la recherche uniquement s'il n'y a pas eu de problème ou s'il existe
        print "CreateTheWatcher: after watcher launch: {} PID={}".format(command,self.WatcherPID)
      except:
        print sys.exc_info() 
        _str="Problème avec la relance du process Watcher LimitTask:\n\n >>Command du SubProcess :\n{}\n\n >>Except err :\n{}".format(command,sys.exc_info())
        win32gui.MessageBox(0,_str,"Erreur de lancement !",4096)
    else:
      threading.Timer(1,self.CreateTheWatcher,[argv,]).start() #on relance la recherche uniquement s'il n'y a pas eu de problème ou s'il existe
      print "CreateTheWatcher:  {} watcher still exits !".format(self.WatcherPID)

  def FindPID(self,exename):
      a = os.popen4('tasklist /FI "IMAGENAME eq '+exename+'"')
      a[0].flush()
      info=[]
      i=0
      thispid=str(os.getpid())
      while True:
        try:
            info.append(a[1].readlines()[3+i].split())
            i+=1
        except:
          break
      info=filter(lambda i:i[1]==thispid,info)
      if info==[]:
        info=[exename,"-1"]
      return (info)
      
if __name__=="__main__":
  
       
  MyPC=LimitTask()
  MyPC.PID=os.getpid()
  MyPC.PATH=os.getcwd()
  MyPC.ARGV=sys.argv
  print  MyPC.PID
  print MyPC.PATH
  print MyPC.ARGV
  argv=sys.argv
  if len(argv)==5 and argv[4][0:10]=="-LimitTask":
    #Cas particulier: après le lancement de LimitTask par utilisateur celui-ci va se dédoubler 
    #avec un argument supplémentaire '-LimitTaskXXXX', XXXX correspond au PID de la TaskLimit principal à l'origine de se dédoublement.
    #Ce cas particulier permttra de relancer le process principal s'il n'existe plus
    #nous sommes donc dans le cas du process LilitTask qui ne fait que relance LimitTask si il ne vois pas deux process 'LimitTask'... :-)
    path = '.\\dist\\' if debug==2 else ''
    LimitTask_name=path+argv[0].split(os.path.sep)[-1:][0].split(".")[0]+".exe"
    LimitTask_PID=int(argv[4][10:])    
    while 1:
      if not psutil.pid_exists(LimitTask_PID): #il n'existe plus qu'un seul LimitTask.exe (killé par quelqu'un/quelque chose), on le relance
        command=[LimitTask_name,argv[1],argv[2],argv[3]]
        try:
          _r=subprocess.Popen(command,creationflags =  DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
          #win32console.FreeConsole()
          time.sleep(1)  
        except:
          win32gui.MessageBox(0,"Problème avec la relance du process principal LimitTask:\n {}...".format(command), "Erreur de lancement !",4096)
        break #on quitte le watcher process après avoir recréer le LimitTask principal, à sa charge de recréer ce watcher...
      time.sleep(0.1)                  

  elif len(argv)!=4:    
    win32gui.MessageBox(0,
u"""Attention ! il y 3 arguments à cette commande:

        1) 'nom de la tache' task présente dans la liste des processus windows
        2) tps de jeu (minutes)
        3) tps remise à zéro (minutes)
        
    Exemple (pour limiter la l'utilisation de la calculatrice à 10 mn toutes les 60mn):
    
               >>{} calc.exe 10 60""".format(argv[0].split(os.path.sep)[-1:][0].split(".")[0]), "Erreur de lancement !",4096) #récupération du dernier élément du fullpath [-1:] d'une liste [0], sans le type du fichier
  else:
    #TODO: vérifier qu'un autre LimitTask.exe n'existe pas avec la même tache
    #TODO:Créer le dédoublement de LimitTask watcher avec -LimitTaskXXXX et lancer un thread qui regarde s'il n'est pas mort
    #TODO: prévoir un argument qui permet de commencer par une attente de remise à zéro
    
    MyPC.CreateTheWatcher(argv)
    MyPC.KillTask(argv[1],int(argv[2]),int(argv[3]))
    
