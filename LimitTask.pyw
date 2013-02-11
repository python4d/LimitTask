#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
LimitTask module is a simple command to limit one specific windows processus (task) for a certain time during a slot of time (subscription).
LimitTask est un module python pour limiter l'usage d'un process windows dans le temps sur une plage de temps déterminé (abonnement).

Usage = 
          python.exe LimitTask.pyw <name_process/task.exe> <max use time> <abonnement/plage de temps>

@author: Python4D/damien.samain@python4d.com
@version: 0.1 bêta - Utilisation du module wmi - Log via module logging fichier LMLog
@version: 0.2 bêta - Abandon du module wmi utilisation des command windows tasklist et taskkill - Sauvegarde PlageTime et TaskTime dans un fichier text LTsave.txt
@todo: minimum gui, password, save data in registery
"""

import time,sys,os
import logging
import win32gui


class LimitTask(object):
  def __init__(self, *args, **kwargs):
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='LimitTask.log',
                    filemode='w+')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
        

  def KillTask(self,Task,NbMin=60,Plage=60*24):
    
    def writesavefile():
      with open("LTsave.txt",'w') as f:
        f.writelines([str(PlageTime),"\n",str(TaskTime)])     
    TaskTime,PlageTime=[0,time.time()]
    if os.path.isfile("LTsave.txt"):
      state=15
    else:
      state=10
    if NbMin>=Plage : 
      win32gui.MessageBox(0, "Attention la Plage de remise à zéro doit Ãªtre Supérieure au temps de la tache/jeu!", "Erreur de lancement !",4096)
      return 1
    #TODO: pas vraiment optimisé, il faudrait reprendre la state machine pour incorporé les deux boucles while en une seule "while true"
    #TODO: on a séparé la state machine qui controle le temps de tache avec celle de la plage 
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
        if state==15: # Récupération des infos du fichier de sauvegarde des données PlgeTime et TaskTime
          self.flag=0 #flag de la tache dThread pour vérifier si on est sortie de la tache
          self.flag_message=0
          with open("LTsave.txt",'r') as f:
            PlageTime,TaskTime=map(float,f.readlines())         
          LastTaskTime=TaskTime
          state=20
        elif state==20:
          process=self.FindPID(Task)
          if process==[]:    
            writesavefile()
            time.sleep(1)
            state=20
          else:          
            if PlageTime+Plage*60<time.time():
              print "Remise à zéro au début Task !\n"            
              state=10 #On reset tout
            else:
              print "Task trouvé! Id={} -Name={}\n".format(process[0][0],process[0][1])
              print "In:%f\n" % TaskTime
              start=time.time()
              state=50
        elif state==50:#task présent reprise du calcul du temps
          process=self.FindPID(process[0][0])
          if process==[]:
            self.flag=0
            logging.info(u"Sortie de {} - Temps total de jeu = {:4.1f} minutes- Temps avant remise à zéro ={:4.1f} minute(s)!".format(Task,TaskTime/60.0,(Plage*60+PlageTime-time.time())/60.0)) 
            print"Out:%f\n" % TaskTime
            LastTaskTime=TaskTime #récupération du temps déjà écoulé
            state=20 #on retourne vérifier qu'il n'y a plus de process en cours
          else:
            writesavefile()
            time.sleep(1)
            TaskTime=LastTaskTime+time.time()-start
            if PlageTime+Plage*60<time.time():
              print "Remise à zéro avant la fin de TaskTime !\n"
              state=10 #On reset tout
#fin de While TaskTime<NbMin*60 => le temps limite et dépassé  
      writesavefile()
      time.sleep(1)  
      process=self.FindPID(Task)
      if process==[]: #pas de process en cours
        if PlageTime+Plage*60<time.time():
          print "Remise à zéro en dehors du jeu!\n"
          TaskTime=0  #permet de rerentrer dans la state machine 
          state=10
      else:
        if not self.flag_message==2:
          win32gui.MessageBox(0, "Tu dois quitter le jeu maintenant - Tu as dépassé les {:4.1f} minute(s) !".format(NbMin), "QUOTA DEPASSE !",4096)
          os.popen4('taskkill /F /PID '+str(process[0][1]))
          self.flag_message=2
        else:
          os.popen4('taskkill /F /PID '+str(process[0][1]))
          logging.info("!Tentative d'entrée dans "+Task+" - Temps restant à attendre ={:4.1f} minute(s)!".format(NbMin,(Plage*60+PlageTime-time.time())/60.0))  
          win32gui.MessageBox(0, "Tu as dépassé tes {:4.0f} minute(s) de jeu,\n tu dois attendre encore {:4.1f} minute(s) pour rejouer !".format(NbMin,(Plage*60+PlageTime-time.time())/60.0), "QUOTA DEPASSE !", 4096)          

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
      info=filter(lambda i:i[1]!=thispid,info)
      return (info)

  
if __name__=="__main__":
  if len(sys.argv)!=4:
    win32gui.MessageBox(0,
u"""Attention ! il y 3 arguments à cette commande:

        1) 'nom de la tache' task présente dans la liste des processus windows
        2) tps de jeu (minutes)
        3) tps remise à zéro (minutes)
        
    Exemple (pour limiter la l'utilisation de la calculatrice à 10 mn toutes les 60mn):
    
               >>{} calc.exe 10 60""".format(sys.argv[0].split(os.path.sep)[-1:][0][:-4]), "Erreur de lancement !",4096) #récupération du dernier élément du fullpath [-1:] d'une liste [0], sans les 4 derniers caractÃšres
  else:
    #TODO: vérifier qu'un autre LimitTask.exe n'existe pas avec la mÃªme tache
    MyPC=LimitTask()
    MyPC.KillTask(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
    
