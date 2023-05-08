import time
import ubinascii
from umqtt.simple import MQTTClient
import random
import esp
from machine import Pin, SoftI2C, ADC, PWM
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
import dht
esp.osdebug(None)
import gc
gc.collect()
import network
import urequests
import math

# Default MQTT server to connect to
SERVER = "broker.mqtt-dashboard.com"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())

#Topicos -NODE-RED
TOPIC1 = b'esp32/dhtReadmqttdata/temperature' 
TOPIC2 = b'esp32/dhtReadmqttdata/humidity'

# Led
led = Pin(2, Pin.OUT)
# Boton
button = Pin(17, Pin.IN, Pin.PULL_UP)

#Configure ADC for ESP32
pot = ADC(Pin(34))
pot.width(ADC.WIDTH_10BIT)
pot.atten(ADC.ATTN_11DB)

#led pwm = Pin(2, Pin.OUT)
led_pwm = PWM(Pin(2), freq=500, duty=0)

#DHT11
sensor = dht.DHT11(machine.Pin(4))

# intervalo de envio de mensajes
last_message = 0
message_interval = 2
    
def reset():
    print("Resetting...")
    time.sleep(5)
    machine.reset()
    
def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(1)
  machine.reset()
  
def main():
    button_state = 0
    led_state = 0
    encendido = 0
    boton = ""
    global last_message
    
    mqttClient = MQTTClient(CLIENT_ID, SERVER, keepalive=60)
    mqttClient.connect()
    print(f"Connected to MQTT  Broker :: {SERVER}")

    while True:
        try:    
            if (time.time() - last_message) > message_interval:
                # obteno la temperatura y la humedad
                sensor.measure()
                print("Temperatura : "+str(sensor.temperature()) + " C°")
                print("Humedad     : "+str(sensor.humidity()) + " %")
                
                # potenciometro
                a = pot.read()
                b = math.trunc(a/4)
                if a > 0:
                    print("Potenciometro : "+str(b))
                    led_pwm.duty(b)
                    encendido = 1
                    
                else:
                    led_pwm.duty(0)
                    encendido = 0
                    
              # boton
                estado_btn = button.value()
                if estado_btn == 1:
                    print("Boton : Apagado  ")
                else:
                    print("Boton : Encendido")
                
                last_State = button_state
                button_state = button.value()
                if button_state == 0:
                    led_state = not(led_state)
                    led_pwm.duty(255)
                    boton = "Encendido"
                    print("LED On")

                    time.sleep(10)
                    led_pwm.duty(0)
                    print("LED Off")
                    boton = "Apagado"
                        
                # publicar datos sensor                
                mqttClient.publish(TOPIC1, str(sensor.temperature()))
                mqttClient.publish(TOPIC2, str(sensor.humidity()))
                
                print()
                last_message = time.time()
        except OSError as e:
            restart_and_reconnect()
    mqttClient.disconnect()
    
if __name__ == "__main__":
    try:
        main()
    except OSError as e:
        print("Error: " + str(e))
        reset()