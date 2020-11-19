#---------------------------- I2C Configuration ----------------------------------
i2c=I2C(0)
i2c.init(I2C.MASTER,baudrate=100000)
i2c=I2C(0,pins=('P22','P21'))

#---------------------------- PySenseButton Configuration ------------------------
PySenseButton=Pin("P14",mode=Pin.IN,pull=Pin.PULL_DOWN)

#---------------------------- Broker credentials ---------------------------------
broker_address="mqtt.mydevices.com"
mqtt_user="your_user"   # enter your mqtt user
mqtt_pass="your_pass"   # enter your mqtt pass
mqtt_client_id="your_client_id" # enter your mqtt client id

# button         -- channel 1
# button_led     -- channel 2
# Temperature    -- channel 3
# Humidity       -- channel 4
# BarPressure    -- channel 5
# Luminosity     -- channel 6
# BoardInc       -- channel 7
# PySenseButton  -- channel 8
#Motion Detecter -- channel 9
#v1/username/things/clientID/cmd/channel
#v1/username/things/clientID/data/channel

#---------------------------- Refresh Sensors Button ---------------------------
subs_button_refresh='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/cmd/1'
publish_button_refresh='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/1'
publish_button_refresh_id='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/response'

#---------------------------- LED Button --------------------------------------------------
subs_button_led='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/cmd/2'
publish_button_led='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/2'
publish_button_led_id='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/response'

publish_temp='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/3'        # -- Temperature
publish_hum='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/4'         # -- Humidity
publish_pres='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/5'        # -- BarPressure
publish_lum='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/6'         # -- Luminosity
publish_inc='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/7'         # -- BoardInc
publish_pybutton='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/8'    # -- PySenseButton
publish_motion='v1/'+mqtt_user+'/things/'+mqtt_client_id+'/data/9'      # -- Motion Detecter

# ----------------------Func for PySenseButton   -------------------------------------------
def check_PySenseButton():
    if PySenseButton()==0: #When PySenseButton is pressed its logical value is '0'
        client.publish(topic=publish_pybutton,msg='digital,d='+str(round(1)))
    elif PySenseButton()==1:#When PySenseButton is NOT pressed its logical value is '1'
        client.publish(topic=publish_pybutton,msg='digital,d='+str(round(0)))

# ------------------- Func for reading BoardInc ---------------------------------------------------------------------
def read_boardinc():
    acc_addr=0x1E
    ctrl1_reg=0x37
    ctrl4_reg=0x00
    ctrl1_addr=0x20
    ctrl4_addr=0x23
    i2c.writeto_mem(acc_addr,ctrl1_addr,ctrl1_reg)
    i2c.writeto_mem(acc_addr,ctrl4_addr,ctrl4_reg)
    out_x_l=i2c.readfrom_mem(acc_addr,0x28,1)
    out_x_h=i2c.readfrom_mem(acc_addr,0x29,1)
    time.sleep(0.1)
    value_x_boardinc=(out_x_h[0]*255)+out_x_l[0]
    value_x_boardinc_deg=(value_x_boardinc*360)/65535
    client.publish(topic=publish_inc,msg='deg,d='+str(round(value_x_boardinc_deg)))
    if ((value_x_boardinc_deg>20)and(value_x_boardinc_deg<340)):   #more than 20deg the motion alarm is activated
        client.publish(topic=publish_motion,msg='motion,d='+str(round(1)))
    elif((value_x_boardinc_deg<=20)or(value_x_boardinc_deg>=340)): #less than 20deg the motion alarm is deactivated
        client.publish(topic=publish_motion,msg='motion,d='+str(round(0)))
    print("roll_GRAUS: "+str(value_x_boardinc_deg)+"º")

# ------------------- Func for reading Temperature, Humidity, Luminosity and Pressure -------------------------------
def read_temp_hum_lum_pres():
    i2c.writeto(0x40,0xF5)
    time.sleep(0.1)
    res_hum=i2c.readfrom(0x40,0x02)
    time.sleep(0.1)
    i2c.writeto(0x40,0xE0)
    time.sleep(0.1)
    res_temp=i2c.readfrom(0x40,0x02)
    time.sleep(0.1)
    value_temp=(((res_temp[0]*255+res_temp[1])*175.72)/65536)-46.85
    value_hum=((((res_hum[0]*255)+res_hum[1])*125)/65536)-6
    client.publish(topic=publish_temp,msg='temp,c='+str(round(value_temp,2)))
    print('Temperature value sent: '+str(value_temp))
    client.publish(topic=publish_hum,msg='hum,p='+str(round(value_hum,2)))
    print('Humidity value sent: '+str(value_hum))

    #------ read Luminosity
    i2c.writeto_mem(0x29,0x80,0x01) # 0x29 -> Luminosity sensor address
    time.sleep(0.2)                 # 0x80 -> sensor's control register address
    if(i2c.readfrom_mem(0x29,0x8c,1)!=0): # check if there is new data
        res_lum=i2c.readfrom_mem(0x29,0x8a,2)
        time.sleep(0.1)
        value_lum=(res_lum[1]*255)+res_lum[0]
        client.publish(topic=publish_lum,msg='lum,lux='+str(round(value_lum)))
        print("Luminosidade value sent: "+str(value_lum)+" lux")

    #----- read Pressure
    mpPress=MPL3115A2(pysense=None,sda='P22',scl='P21',mode=PRESSURE)
    pressure=mpPress.pressure()/100
    client.publish(topic=publish_pres,msg='bp,hpa='+str(round(pressure,2)))
    print("Pressure (hPa): "+str(pressure))

# ------------------- Func that takes actions when one of the buttons in the broker is pressed ---------------------------------------
def broker_buttons(topic,msg):
    if topic==b"v1/93cae110-1031-11ea-a38a-d57172a4b4d4/things/b1cdfc10-1031-11ea-a38a-d57172a4b4d4/cmd/2": # subs_button_led
        msg_part=msg.decode().split(',')
        client.publish(publish_button_led, msg_part[1]) #refresh button state
        client.publish(publish_button_led_id,"ok,"+msg_part[0]) #send the button id to Cayenne to refresh button state
        if msg_part[1]=='1':
            pycom.rgbled(0x7f0000) # red
        elif msg_part[1]=='0':
            pycom.rgbled(0) # off
    elif topic==b"v1/93cae110-1031-11ea-a38a-d57172a4b4d4/things/b1cdfc10-1031-11ea-a38a-d57172a4b4d4/cmd/1": #subs_button_refresh
        msg_part=msg.decode().split(',')
        client.publish(publish_button_refresh,msg_part[1]) #refresh button state
        client.publish(publish_button_refresh_id,"ok,"+msg_part[0]) #send the button id to Cayenne to refresh button state
        if msg_part[1]=='1':
            read_temp_hum_lum_pres() #call funcion to read temperature, humidity, luminosity, barometric pressure and publish results

# ------------------- WIFI Connection ------------------------------------------------------------------------------------------------
wlan.connect('your_SSID',auth=(3,'your_WiFi_password'),timeout=5000)    # enter your network credentials
while not wlan.isconnected():
    machine.idle() # save power while waiting
print('WLAN connection succeeded!')

# ------------------- UMQTT Connection and callbacks subscritions ---------------------------------------------
client=MQTTClient(client_id=mqtt_client_id,server=broker_address,user=mqtt_user,password=mqtt_pass,port=1883)
client.set_callback(broker_buttons)
client.connect()
print('Connected to MQTT.fx Broker: '+str(broker_address))
client.subscribe(topic=subs_button_led)
client.subscribe(topic=subs_button_refresh)

# ------------------- Infinite loop so that the program keeps running -----------------------------------------
timer_sensors=0
while True:
    timer_sensors+=1
    check_PySenseButton()
    read_boardinc()
    time.sleep(1)
    client.check_msg()
    if(timer_sensors==300): #5min have passed
        read_temp_hum_lum_pres()
        timer_sensors=0
