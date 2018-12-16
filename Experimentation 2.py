# Projet - Mon premier interface avec des composants externes
#          (ex: LED)
# Date:    2018-11-11
# Par:     SGu
#
from gpiozero import *
import RPi.GPIO as GPIO

import time

CONST_NO_GPIO_RED_LED = 18
CONST_NO_GPIO_BLUE_LED = 17
CONST_NO_GPIO_GREEN_LED = 27

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

def flash_led(lst_LED_A, mode_flash):
    CONST_DELAI_LUMIERE_SECONDE= 0.2
    CONST_NBR_TOUR=2
    
    #Boucle dans le tableau de LED et allume et éteint
    for i in range(1,CONST_NBR_TOUR+1):   
        for LED in lst_LED_A:
            LED.on()
            time.sleep(CONST_DELAI_LUMIERE_SECONDE)
            LED.off()
        i=i+1


    #for LED in lst_LED:
     #   print(str(LED.Closed))
    
    
    return

#####
#  Outil pour lire le MCP3008 qui converti un signal analogique en numérique
#   --> Analog Digital Converter ADC
#
#   adcnum: Le numéro du canal analogique à convertir (entier entre 0 à 7)
#
#   Variables
#      clockpin (#CLK):   Sert à synchroniser les lectures et communications
#      mosipin (#Din):    Sert à informer le processeur quel canal (adcnum) il faut lire sur 5 bits ???
#      misopin (#Dout):   Sert à lire la valeur du canal (adcnum) convertie sur 11 bits
#      cspin  (#CD/SHDN):  ??? Sert à débuter (false = occupé et true = disponible) une instruction et 
#
#   2do: Intégrer une gestion des erreurs, vérifier les paramètres
#
#####
#fonction lisant les donnees SPI de la puce MCP3008, parmi 8 entrees, de 0 a 7
def readADC(adcnum):
        #Vérifie le paramètre
        if ((adcnum > 7) or (adcnum < 0)):
            return -1   # Sortie pcq le numéro de canal est hors bornes

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


        ###
        #  Réassigne les constantes vers les variables par "parresse" afin d'éviter de
        #  le reste de la fonction qui vient d'une fonction récupérer sur le web
        mosipin = SPIMOSI
        misopin = SPIMISO
        clockpin = SPICLK
        cspin = SPICS
        
        # definition de l'interface SPI
        GPIO.setup(SPIMOSI, GPIO.OUT)
        GPIO.setup(SPIMISO, GPIO.IN)
        GPIO.setup(SPICLK, GPIO.OUT)
        GPIO.setup(SPICS, GPIO.OUT)
        #
        #   Fin de l'initialisation
        #####



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

#### Début du programme
print("Début du programme \n")

# Fait flasher les lumières pour attirer l'attention
flash_led(lst_LED, CONST_MODE_FLASH)

#Definition du ADC utilise (broche du MCP3008). Cette valeur peut aller de 0 à 7.
adcnum = 0
# Lecture de la valeur brute du capteur
read_adc0 = readADC(adcnum)
if read_adc0==-1 :
    print("\tUne erreur c'est produite")
else:
    # conversion de la valeur brute lue en milivolts = ADC * ( 3300 / 1024 )
    millivolts = read_adc0 * ( 3300.0 / 1024.0)
    print("\tValeur brute : %s" % read_adc0)
    print("\tTension : %s millivolts" % millivolts)

# Fait flasher les lumières pour attirer l'attention
flash_led(lst_LED, CONST_MODE_FLASH)

print("Fin du programme \n")

