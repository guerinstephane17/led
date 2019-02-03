# Projet - Mon premier interface avec des composants externes
#          (ex: LED)
# Date:    2018-11-11
# Par:     SGu
#
from gpiozero import LED, Button
from time import gmtime, strftime, time, sleep

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import json


####
#  Déclaration des paramètre pour communication dans le serveur MQTT
#
#####
# BROKER_ADRESSE = "192.168.1.148" #Adresse du serveur MQTT, TODO faire une fonction pour get IP Local
BROKER_ADRESSE = "demo.thingsboard.io"    # Adresse du serveur MQTT pour faire démonstration avec service live de thingsboard
TOPIC = "v1/devices/me/telemetry"         # L'identifiant du channel de communication
access_token = "escouadeVerte"            # L'acces token fournit par le serveur MQTT associé au channel
password=""

data=dict()                               # Déclare l'objet tableau associatif clé --> valeur pour générer
                                          #   la structure json


#####
#
#    Récupère la communication avec le serveur
#
#####
def saveMQTTConnection(mqttConnection):
    
    mqttConnection.reconnect()
    
    return 

#
# Initialisation du client MQTT
#
client = mqtt.Client("Pi-Residu")               # L'identifiant du client
client.username_pw_set(access_token, password)
client.connect(BROKER_ADRESSE)

#
#####


#####
#  Récupère la date et l'heure actuelles en format Greenwitch, retourne un string.
#
#  localTime :  Vrai = Retourne l'heure GMT
#               Faux = [valeur par défaut] Retourne l'heure locale configurée dans le système d'exploitation
#
#####
def getTime(localTime = False) :   
    
    if localTime == True:
        actTime = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime(time()))
    else:
        actTime = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime(time()))
    
    return actTime



#####
#  Outil pour lire le MCP3008 qui converti un signal analogique en numérique
#   --> Analog Digital Converter ADC
#
#   adcnum: Le numéro du canal analogique à convertir (entier entre 0 à 7)
#   clockpin (#CLK):   Serial Clk - Sert à synchroniser les lectures et communications
#   mosipin (#Din):    Serial Data In - Sert à informer le processeur quel canal (adcnum) il faut lire sur 5 bits ???
#   misopin (#Dout):   Serial Data Out - Sert à lire la valeur du canal (adcnum) convertie sur 11 bits
#   cspin  (#CS/SHDN):  Chip select/shutdown input - Sert à débuter (false = occupé et true = disponible) une instruction 
#
#   2do: Intégrer une gestion des erreurs, vérifier les paramètres
#
#####
#fonction lisant les donnees SPI de la puce MCP3008, parmi 8 entrees, de 0 a 7
def readADC(adcnum, clockpin, mosipin, misopin, cspin):
        #Vérifie le paramètre
        if ((adcnum > 7) or (adcnum < 0)):
            return -1
        #####
        #   Initialise l'ADC
        #
        GPIO.output(cspin, True)
        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)	 # bring CS low
        #
        #####
        
        #####
        #   Envoie l'instruction à l'ADC pour indiquer quel canal à lire (0 à 7)
        #
        #
        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        #   0x18 = 0001 1000
        #   Fusionne la valeur en binaire du numéro de la pin à lire pour obtenir
        #        00011XXX où XXX = valeur en binaire de adcnum       
        commandout <<= 3	# we only need to send 5 bits here
        #   Décale les bits à gauche pour avoir les 5 premiers bits
        #   pourquoi seulement 5?
        #
        #   Envoi un "true" pour chaque bit à 1 de la valeur commandout
        for i in range(5):
            if (commandout & 0x80):   #0x80 = 1000 0000 binaire = 128 décimal
                GPIO.output(mosipin, True)
            else:
                GPIO.output(mosipin, False)
            commandout <<= 1
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)
        #
        #   L'ADC connait le canal à lire --> adcnum
        #   
        #####
 
        #####
        #   Fait la lecture de la valeur en lisant les 11 bits
        #
        #
        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)
            adcout <<= 1
            if (GPIO.input(misopin)):
                adcout |= 0x1
        #
        #   Lecture terminée
        #####
        
        GPIO.output(cspin, True)
        adcout /= 2	   # first bit is 'null' so drop it
        
        
        return adcout

#### Fin fonction readADC
  

#####
#   Montage du ADC
#
# Les numéros de pins GPIO doivent etre modifies pour correspondre aux broches utilisées
# Vdd   Courrant borne +
# Vref  Courrant borne +
# AGND  Courrant borne masse -
SPICLK = 24  # CLK
SPIMISO = 25 # Dout
SPIMOSI = 8  # Din
SPICS = 7    # CS/SHDN
# DGND  Courrant borne masse -
#
#   Fin montage
#####

# definition de l'interface SPI
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

#
#Définition du ADC utilise (broche du MCP3008). Cette valeur peut aller de 0 à 7
# sous forme d'une structure dictionnaire [Nom]:[PIN]
#
CONST_ADC_NOM_BALANCE_RESIDU="KG_RESIDU"
CONST_ADC_PIN_BALANCE_RESIDU=0
CONST_ADC_NOM_BALANCE_COMPOST="KG_COMPOST"
CONST_ADC_PIN_BALANCE_COMPOST=1
CONST_ADC_NOM_BALANCE_RECYCLAGE="KG_RECYCLAGE"
CONST_ADC_PIN_BALANCE_RECYCLAGE=2

#
# Construit un tableau associatif des balances dans l'ordre souhaité
#
dict_BALANCE=dict()
dict_BALANCE[CONST_ADC_NOM_BALANCE_RESIDU]=CONST_ADC_PIN_BALANCE_RESIDU
dict_BALANCE[CONST_ADC_NOM_BALANCE_COMPOST]=CONST_ADC_PIN_BALANCE_COMPOST
dict_BALANCE[CONST_ADC_NOM_BALANCE_RECYCLAGE]=CONST_ADC_PIN_BALANCE_RECYCLAGE


#####
#  Définition des LED
#
#      ID des GPIO pour LED
#
CONST_NO_GPIO_RED_LED = 18
CONST_NO_GPIO_BLUE_LED = 17
CONST_NO_GPIO_GREEN_LED = 27

#
# Construit un tableau des lumières dans l'ordre
# préféré d'affichage
#
# Construit un tableau des LED avec les index des noms de balances pour
#   permettre d'afficher une interaction personne-machine lors d'une lecture de la balance
#
dict_LED=dict()
dict_LED[CONST_ADC_NOM_BALANCE_RESIDU]=LED(CONST_NO_GPIO_RED_LED)
dict_LED[CONST_ADC_NOM_BALANCE_COMPOST]=LED(CONST_NO_GPIO_GREEN_LED)
dict_LED[CONST_ADC_NOM_BALANCE_RECYCLAGE]=LED(CONST_NO_GPIO_BLUE_LED)


CONST_DELAI_LUMIERE_SECONDE= 0.2

#####
#  Signale aux humains ton état en faisant un
#  truc visuel avec les LED
#
#   dict_Tous_LED: un dictionnaire de LED
#   mode_flash: une valeur sur le patern de flash
#
#   2do: Intégrer une gestion des erreurs, vérifier les paramètres
#
#####

#
#  Mode d'affichage pour flasher les lumières
#
CONST_MODE_FLASH_INIT=1                          # Allume successivement toutes les LED dans l'ordre de la liste
CONST_MODE_ALL_ON=2                              # Allume toutes les LED
CONST_MODE_ALL_OFF=3                             # Éteint toutes les LED
CONST_MODE_FLASH_ALL=4                           # Flash tous les LED en même temps
CONST_MODE_FLASH_UNIQUE=5                        # Flash une fois la LED


def flash_led(dict_Tous_LED, mode_flash, interval = CONST_DELAI_LUMIERE_SECONDE, led_a_clignote = CONST_ADC_NOM_BALANCE_RESIDU):
    CONST_NBR_FLASH=3   # Nombre flash
    CONST_NBR_TOUR=1    #
    if mode_flash == CONST_MODE_FLASH_INIT:      
         #   CONST_TOLERANCE_INTERVAL=0.003
         # Tolérance est à 1% de la différence min et max délai de seconde
        CONST_TOLERANCE_INTERVAL = 0.01*(CONST_INTERVAL_MAXIMUM_SEC - CONST_INTERVAL_MINIMUM_SEC)
        borneMin = CONST_INTERVAL_MINIMUM_SEC + CONST_TOLERANCE_INTERVAL
        borneMax = CONST_INTERVAL_MAXIMUM_SEC - CONST_TOLERANCE_INTERVAL
        
        
        if interval > borneMin and interval < borneMax:
            # Intérieur des bornes alors Boucle dans le tableau de LED et allume et éteint en boucle les LED 
            for i in range(1,CONST_NBR_TOUR+1):   
                for key in dict_Tous_LED:
                    dict_Tous_LED[key].on()
                    sleep(interval)
                    dict_Tous_LED[key].off()
                i=i+1
        elif interval <= borneMin:
            #Interval trop petit alors flash le premier LED à la fréquence par défaut        
            dict_Tous_LED[0].on()
            sleep(CONST_DELAI_LUMIERE_SECONDE)
            dict_Tous_LED[0].off()
            sleep(CONST_DELAI_LUMIERE_SECONDE)
            
        elif interval >= borneMax:
            #Interval trop grand alors flash le dernier LED à la fréquence par défaut
            dict_Tous_LED[-1].on()
            sleep(CONST_DELAI_LUMIERE_SECONDE)
            dict_Tous_LED[-1].off()
            sleep(CONST_DELAI_LUMIERE_SECONDE)
        else:
             #Problème non prévu et condition normalement impossible
             print ("Condition impossible: impossible de flasher")
             
    elif mode_flash == CONST_MODE_ALL_ON:
        # Boucle dans le tableau de LED et allume tous les LED
        for key in dict_Tous_LED:
            dict_Tous_LED[key].on()
        
    elif mode_flash == CONST_MODE_ALL_OFF:
        # Boucle dans le tableau de LED et allume tous les LED 
        for key in dict_Tous_LED:
            dict_Tous_LED[key].off()
    
    elif mode_flash == CONST_MODE_FLASH_ALL:
        # Flash toutes les lumières en même temps
        for key in dict_Tous_LED:
            dict_Tous_LED[key].off()


        for i in range(1,CONST_NBR_FLASH+1):   
            for key in dict_Tous_LED:
                dict_Tous_LED[key].on()
            sleep(interval)
            for key in dict_Tous_LED:
                dict_Tous_LED[key].off()
            i=i+1
            
    elif mode_flash == CONST_MODE_FLASH_UNIQUE:
        # Flash une seule lumière
        for i in range(1,CONST_NBR_FLASH+1):   
            dict_Tous_LED[led_a_clignote].on()
            sleep(interval)
            dict_Tous_LED[led_a_clignote].off()
            i=i+1

    else:  # Type de flasher inconnu
            #Problème non prévu et condition normalement impossible
            print ("Mode de impossible de flasher")
          
 
    
    return


#####
#  Définition des boutons
# ID des GPIO pour bouton
#

CONST_BTN_NOM_LECTURE = "Lecture"
CONST_BTN_NO_GPIO_LECTURE = 2
#
# Construit un tableau des lumières dans l'ordre
# préféré d'affichage
#
# Construit un tableau des LED avec les index des noms de balances pour
#   permettre d'afficher une interaction personne-machine lors d'une lecture de la balance
#
dict_BTN=dict()
dict_BTN[CONST_BTN_NOM_LECTURE]=Button(CONST_BTN_NO_GPIO_LECTURE)
print("Liste des boutons: %s" % dict_BTN)


#####
#  Définition pour simuler la balance avec des gradateurs
#
#
interval = CONST_DELAI_LUMIERE_SECONDE         # Fixe la valeur initiale pour rythme d'affichage des LED

CONST_VALEUR_MAXIMUM_GRADATEUR = 1023.5
CONST_VALEUR_MINIMUM_GRADATEUR = 0
CONST_INTERVAL_MAXIMUM_SEC = 0.7
CONST_INTERVAL_MINIMUM_SEC = 0.07

CONST_FCT_CONVERSION= (CONST_INTERVAL_MAXIMUM_SEC-CONST_INTERVAL_MINIMUM_SEC)/(CONST_VALEUR_MAXIMUM_GRADATEUR-CONST_VALEUR_MINIMUM_GRADATEUR)
print("Facteur de conversion: %s" % CONST_FCT_CONVERSION)

#   Fin des paramètres de simulation
#####

print("dict_LED= %s " % dict_LED)
print("dict_Balance= %s " % dict_BALANCE)


# Fait flasher les lumières pour initialiser, attirer l'attention et faire une rétroaction personne-machine
flash_led(dict_LED, CONST_MODE_FLASH_INIT)

# Attend le go du piton
#lst_button[0].wait_for_press()
   
#print("\tListe des balances: %s" % dict_BALANCE[1])

#while interval > CONST_INTERVAL_MINIMUM_SEC:

while True:
    print("\tOn attend le bouton ;-)")
    dict_BTN[CONST_BTN_NOM_LECTURE].wait_for_press()
    
    for key in dict_BALANCE.keys():
        # Lecture de la valeur des balances
        flash_led(dict_LED, CONST_MODE_FLASH_UNIQUE,CONST_DELAI_LUMIERE_SECONDE,key)
        data[key]=readADC(dict_BALANCE[key], SPICLK, SPIMOSI, SPIMISO, SPICS)
        
    ### Pour simuler tester une troisième balance on augmente la lecture de 28%
    #data[CONST_ADC_NOM_BALANCE_RECYCLAGE]=data[key]*1.28
        
    print("\tValeurs du tableau data: %s " % data)
    
    data_out=json.dumps(data)       # Converti en jason le data pour publier sur le serveur
    # Publie la lecture sur le serveur
    
    mqtt_retour = client.publish(TOPIC,data_out)
    print("%s |\t\tValeur de retour: %s" % (getTime(), mqtt_retour.rc))
    print("%s |\t\tValeur objet de retour: %s" % (getTime(), mqtt_retour))
    if mqtt_retour.rc != mqtt.MQTT_ERR_SUCCESS:
        # Si erreur tente de récupérer
        if not saveMQTTConnection(client):
                print("%s |\t\tConnection perdue" % getTime())
 
    #print("\tValeur de retour: %s" % client.publish(TOPIC,data_out))


    #if read_adc0 == -1 :
    #    print("\tUne erreur c'est produite")
    #    interval = CONST_INTERVAL_MINIMUM_SEC -1  ## pour arrêter la boucle
      
    #else:
        # conversion de la valeur brute lue en milivolts = ADC * ( 3300 / 1024 )
        # millivolts = read_adc0 * ( 3300.0 / 1024.0)
        # print("\tTension : %s millivolts" % millivolts)
        
        
        #####
        #  Pour simuler une activité et informer l'humain pendant le débogage
        #    accélère ou décélère le rythme d'affichage des lumières en fct du gradateur
        #
     #   interval_prec = interval
     #   interval = ((read_adc0-CONST_VALEUR_MINIMUM_GRADATEUR)/(CONST_VALEUR_MAXIMUM_GRADATEUR-CONST_VALEUR_MINIMUM_GRADATEUR) * (CONST_INTERVAL_MAXIMUM_SEC-CONST_INTERVAL_MINIMUM_SEC))+CONST_INTERVAL_MINIMUM_SEC


        #Affiche des résultats seulement s'il y a un changement       
    #  if interval != interval_prec:
            #  Construire le JSON à publier
    #        data_out=json.dumps(data)
    #        print("\t##### ")
    #        print("\tValeur de retour: %s" % client.publish(TOPIC,data_out))
            
    #        print("\tValeur brute : %s" % read_adc0)
    #        print("\tIntervale: %s" % interval)
            

            
        
print("Fin du programme \n")





