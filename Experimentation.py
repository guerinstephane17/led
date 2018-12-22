# Projet - Mon premier interface avec des composants externes
#          (ex: LED)
# Date:    2018-11-11
# Par:     SGu
#
from gpiozero import LED, Button

import RPi.GPIO as GPIO

import time

#
# ID des GPIO pour LED
#
CONST_NO_GPIO_RED_LED = 18
CONST_NO_GPIO_BLUE_LED = 17
CONST_NO_GPIO_GREEN_LED = 27

#
# ID des GPIO pour bouton
#
CONST_NO_GPIO_BUTTON_1 = 2
#lst_button=[]
#lst_button.append(Button(CONST_NO_GPIO_BUTTON_1))
#button=Button(CONST_NO_GPIO_BUTTON_1)

#
# Construit un tableau des lumières dans l'ordre
# préféré d'affichage
#
lst_LED=[]
lst_LED.append(LED(CONST_NO_GPIO_RED_LED))
lst_LED.append(LED(CONST_NO_GPIO_BLUE_LED))
lst_LED.append(LED(CONST_NO_GPIO_GREEN_LED))

    
#####
#  Mode d'affichage pour flasher les lumières
#####
CONST_MODE_FLASH=1
CONST_DELAI_LUMIERE_SECONDE= 0.2


#####
#  Signale aux humains ton état en faisant un
#  truc visuel avec les LED
#
#   lst_LED_A: une liste de tableau de LED
#   mode_flash: une valeur sur le patern de flash
#
#   2do: Intégrer une gestion des erreurs, vérifier les paramètres
#
#####

def flash_led(lst_LED_A, mode_flash, interval):

    CONST_NBR_TOUR=1
 #   CONST_TOLERANCE_INTERVAL=0.003
     # Tolérance est à 1% de la différence min et max délai de seconde
    CONST_TOLERANCE_INTERVAL = 0.01*(CONST_INTERVAL_MAXIMUM_SEC - CONST_INTERVAL_MINIMUM_SEC)
    borneMin = CONST_INTERVAL_MINIMUM_SEC + CONST_TOLERANCE_INTERVAL
    borneMax = CONST_INTERVAL_MAXIMUM_SEC - CONST_TOLERANCE_INTERVAL
    
    
    if interval > borneMin and interval < borneMax:
        # Intérieur des bornes alors Boucle dans le tableau de LED et allume et éteint en boucle les LED 
        for i in range(1,CONST_NBR_TOUR+1):   
            for LED in lst_LED_A:
                LED.on()
                time.sleep(interval)
                LED.off()
            i=i+1
    elif interval <= borneMin:
        #Interval trop petit alors flash le premier LED à la fréquence par défaut        
        lst_LED_A[0].on()
        time.sleep(CONST_DELAI_LUMIERE_SECONDE)
        lst_LED_A[0].off()
        time.sleep(CONST_DELAI_LUMIERE_SECONDE)
        
    elif interval >= borneMax:
        #Interval trop grand alors flash le dernier LED à la fréquence par défaut
        print ("Interval trop grand %s" % interval)
        lst_LED_A[-1].on()
        time.sleep(CONST_DELAI_LUMIERE_SECONDE)
        lst_LED_A[-1].off()
        time.sleep(CONST_DELAI_LUMIERE_SECONDE)
    else:
         #Problème non prévu et condition normalement impossible
         print ("Condition impossible: pas possible de flasher")

    #for LED in lst_LED:
     #   print(str(LED.Closed))
    
    
    return

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


#definition du ADC utilise (broche du MCP3008). Cette valeur peut aller de 0 à 7.
adcnum = 0
interval = CONST_DELAI_LUMIERE_SECONDE

CONST_VALEUR_MAXIMUM_GRADATEUR = 1023.5
CONST_VALEUR_MINIMUM_GRADATEUR = 0
CONST_INTERVAL_MAXIMUM_SEC = 0.7
CONST_INTERVAL_MINIMUM_SEC = 0.07

CONST_FCT_CONVERSION= (CONST_INTERVAL_MAXIMUM_SEC-CONST_INTERVAL_MINIMUM_SEC)/(CONST_VALEUR_MAXIMUM_GRADATEUR-CONST_VALEUR_MINIMUM_GRADATEUR)
print("Facteur de conversion: %s" % CONST_FCT_CONVERSION)

# Fait flasher les lumières pour initialiser
flash_led(lst_LED, CONST_MODE_FLASH, interval)

# Attend le go du piton
#lst_button[0].wait_for_press()


#while interval > CONST_INTERVAL_MINIMUM_SEC:
while 1==1:
    # Lecture de la valeur brute du capteur
    read_adc0 = readADC(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)

    if read_adc0 == -1 :
        print("\tUne erreur c'est produite")
        interval = CONST_INTERVAL_MINIMUM_SEC -1  ## pour arrêter la boucle
      
    else:
        # conversion de la valeur brute lue en milivolts = ADC * ( 3300 / 1024 )
        # millivolts = read_adc0 * ( 3300.0 / 1024.0)
        # print("\tTension : %s millivolts" % millivolts)
        
        interval_prec= interval


        interval = ((read_adc0-CONST_VALEUR_MINIMUM_GRADATEUR)/(CONST_VALEUR_MAXIMUM_GRADATEUR-CONST_VALEUR_MINIMUM_GRADATEUR) * (CONST_INTERVAL_MAXIMUM_SEC-CONST_INTERVAL_MINIMUM_SEC))+CONST_INTERVAL_MINIMUM_SEC
        #interval = read_adc0 * CONST_FCT_CONVERSION 
        #Affiche des résultats seulement s'il y a un changement
        if interval != interval_prec:
            print("\tValeur brute : %s" % read_adc0)
            print("\tIntervale: %s" % interval)

        # Fait flasher les lumières à la vitesse ajustée 
        flash_led(lst_LED, CONST_MODE_FLASH, interval)
            
        
print("Fin du programme \n")
print("\tValeur brute : %s" % read_adc0)
print("\tIntervale: %s" % interval)




