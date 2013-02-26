#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
LimitTask module is a simple command to limit one specific windows processus (task) for a certain time during a slot of time (subscription).
LimitTask est un module python pour limiter l'usage d'un process windows dans le temps sur une plage de temps d�termin� (abonnement).

Usage = 
          python.exe LimitTask.pyw <name_process/task.exe> <max use time> <abonnement/plage de temps>

@author: Python4D/damien.samain@python4d.com
@version: 0.1 b�ta - Utilisation du module wmi - Log via module logging fichier LMLog
@version: 0.2 b�ta - Abandon du module wmi utilisation des commandes windows tasklist et taskkill - Sauvegarde PlageTime et TaskTime dans un fichier text LTsave.txt
@version: 0.3 b�ta - Cr�ation de boite de dialogue �ph�m�re - abandon de logging
@todo: minimum gui, password, save data in registery
"""

import time,sys,os,subprocess
# Importation des constantes windows (win32con) et wrapper of win32's functions 
#@note: http://sourceforge.net/projects/pywin32/
import win32gui,win32con


class LimitTask(object):
  
  def LimitTask(self,Task,NbMin=60,Abonnement=60*24):
    
    def writesavefile():
      with open("LTsave.txt",'w') as f:
        f.writelines([str(PlageTime),"\n",str(TaskTime)])     
        
    TaskTime,PlageTime=[0,time.time()]
    if os.path.isfile("LTsave.txt"):
      state=15
    else:
      state=10

    #TODO: il faudrait reprendre la state machine pour incorporer les deux boucles while en une seule "while true"
    #TODO: on a s�par� la state machine qui controle le temps de tache avec celle de la plage 
    while True: #Boucle infinie g�rant la v�rification de la plage et tasktime
      print "WHILE TRUE => state={:d}, tasktime={:4.1f}, plagetime={:4.1f}".format(state,TaskTime,time.time()-PlageTime)
      while TaskTime<NbMin*60: #boucle (statemachine) g�rant le temps d'entr�e et sortie dans la tache
        print "WHILE TaskTime<NbMin*60 => state={:d}, tasktime={:4.1f}, plagetime={:4.1f}".format(state,TaskTime,time.time()-PlageTime)
        if state==10: # init des flags et Temps
          self.flag=0 #flag de la tache dThread pour v�rifier si on est sortie de la tache
          self.flag_message=0
          TaskTime=0  
          PlageTime=time.time()
          LastTaskTime=0
          state=20
        if state==15: # R�cup�ration des infos du fichier de sauvegarde des donn�es PlgeTime et TaskTime
          self.flag=0 #flag de la tache dThread pour v�rifier si on est sortie de la tache
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
            if PlageTime+Abonnement*60<time.time():
              print u"Remise � z�ro au d�but Task !"            
              state=10 #On reset tout
            else:
              print u"Task trouv�! Id={}-Name={}".format(process[0][0],process[0][1])
              start=time.time()
              state=50
        elif state==50:#task pr�sent reprise du calcul du temps
          process=self.FindPID(process[0][0])
          if process==[]:
            self.flag=0
            print(u"Sortie de {} - Temps total de jeu = {:4.1f} minutes- Temps avant remise � z�ro ={:4.1f} minute(s)!".format(Task,TaskTime/60.0,(Abonnement*60+PlageTime-time.time())/60.0)) 
            LastTaskTime=TaskTime #r�cup�ration du temps d�j� �coul�
            state=20 #on retourne v�rifier qu'il n'y a plus de process en cours
          else:
            writesavefile()
            time.sleep(1)
            TaskTime=LastTaskTime+time.time()-start
            if PlageTime+Abonnement*60<time.time():
              print u"Remise � z�ro avant la fin de TaskTime !"
              state=10 #On reset tout
#fin de While TaskTime<NbMin*60 => le temps limite et d�pass�  
      writesavefile()
      time.sleep(1)  
      process=self.FindPID(Task)
      if process==[]: #pas de process en cours
        if PlageTime+Abonnement*60<time.time():
          print u"Remise � z�ro en dehors du jeu!\n"
          TaskTime=0  #permet de rerentrer dans la state machine 
          state=10
      else:
        if not self.flag_message==2:
          self.MessageBoxTimeout(0, u"Tu dois quitter le jeu maintenant - Tu as d�pass� les {:4.1f} minute(s) !".format(NbMin), "LimitTask - QUOTA DEPASSE !",4096,10)
          subprocess.check_output('taskkill /F /PID '+str(process[0][1]))
          self.flag_message=2
        else:
          subprocess.check_output('taskkill /F /PID '+str(process[0][1]))
          self.MessageBoxTimeout(0, u"Tu as d�pass� tes {:4.0f} minute(s) de jeu,\n tu dois attendre encore {:4.1f} minute(s) pour rejouer !".format(NbMin,(Abonnement*60+PlageTime-time.time())/60.0), "LimitTask - QUOTA DEPASSE !", 4096,10)          

  def FindPID(self,exename):
      a = subprocess.check_output('tasklist /FI "IMAGENAME eq '+exename+'"').split("\r\n")
      info=[]
      i=0
      thispid=str(os.getpid())
      while len(a)>=3 and a[3+i].split()!=[]:
        info.append(a[3+i].split())
        i+=1
      info=filter(lambda i:i[1]!=thispid,info)
      return (info)
  def MessageBoxTimeout(self,parent,title,message,options=win32con.MB_SYSTEMMODAL,timeout=10):
    """
    Cr�ation d'une boite de dialogue (#32770 class windows)
    Attente d'un timeout
    Fermeture de la boite de dialogue
    """
    from threading import Thread as Process
    _p=Process(target=win32gui.MessageBox, args=(parent,title,message,options))
    _p.start()
    time.sleep(timeout)
    hwnd=win32gui.FindWindow(32770,u"LimitTask - QUOTA DEPASSE !")
    win32gui.PostMessage(hwnd,win32con.WM_CLOSE)
  
if __name__=="__main__":
  if len(sys.argv)!=4:
    win32gui.MessageBox(0,
u"""Attention ! il y 3 arguments � cette commande:

        1) 'nom de la tache' task pr�sente dans la liste des processus windows
        2) Temps utilisation max. de l'ex�cutable - tps de jeu (minutes)
        3) Temps du renouvelement de l'abonnement - tps remise � z�ro (minutes)
        
    Exemple (pour limiter la l'utilisation de la calculatrice � 10 mn toutes les 60mn):
    
               >>{} calc.exe 10 60""".format(sys.argv[0].split(os.path.sep)[-1:][0][:-4]), u"Erreur de lancement !",4096) #r�cup�ration du dernier �l�ment du fullpath [-1:] d'une liste [0], sans les 4 derniers caractères
  elif int(sys.argv[2])>=int(sys.argv[3]) : 
      win32gui.MessageBox(0, u"Attention la Plage de remise � z�ro doit �tre Sup�rieure au temps de la tache/jeu!", u"LimitTask - Erreur de lancement !",4096)
  else:
    #TODO: v�rifier qu'un autre LimitTask.exe n'existe pas avec la même tache
    MyPC=LimitTask()
    MyPC.LimitTask(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
    
