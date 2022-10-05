from time import sleep
import webbrowser
from  kivymd.app import MDApp 
from kivy.lang import Builder
from kivymd.uix.button import MDFlatButton
import json
import os
import pickle
import threading
import socket
from jnius import autoclass
import xmltodict
from plyer import tts
import requests
from kivy.clock import Clock
from requests.auth import HTTPBasicAuth
from includes import config, file_share
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineIconListItem, IconRightWidget, OneLineListItem
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivymd.uix.card import MDCard
from kivymd.uix.templates import StencilWidget
from kivymd.uix.templates import ScaleWidget
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty

Window.keyboard_anim_args = {'d': .2, 't': 'in_out_expo'}
Window.softinput_mode = "below_target"
#Window.size = (1080/2, 2134/2)
encoding = 'ascii'
buffer = 1024
class ConnectScreen(Screen):
    pass

class MainScreen(Screen):
    pass

class MusicScreen(Screen):
    def __init__(self, **kw):
        Clock.schedule_interval(self.update_music,15)
        super().__init__(**kw)
    def get_artwork(self,art,name,artist):
        symbols = '`~!@#$%^&*()_+-={[]}:;"\'<>,./?'
        for i in symbols:
            if i in name:
                name = name.replace(i,"")
            if i in artist:
                artist = artist.replace(i,"")
        if " "in name : name =  name.replace(" ","")
        if " "in artist : artist = artist.replace(" ","")
        path = "{}{}".format(name,artist)
        if os.path.exists(path):
            return path
        art = art.split("file://")[-1]
        msg="ARTWORK~{}".format(art)
        config.client.send(msg.encode(encoding))
        try:   
            os.system("rm -f art")
        except:
            print("not removed")
        sleep(1)
        file_share.recieve(host=config.ip,path=path)

        return path

    def update_music(self,_):
        if config.client:
            Clock.schedule_once(self.updater_music,1)

    def updater_music(self,_):
        print("update music")
        song = self.get_current_song()
        if song['artwork'] !='avatar.jpg':
            pth = self.get_artwork(song['artwork'],song['name'],song['artist'])
        if song == None:
            song = "Offline"

        self.ids.songname.text= song['name']
        self.ids.artistname.text= song['artist']
        sleep(1)
        if song['artwork'] !='avatar.jpg':
            self.ids.circle_img.source = pth     

        else:
            self.ids.circle_img.source = "avatar.jpg"

    def get_current_song(self):
        d={'name':'Offline','artist':'Unknown','artwork':'avatar.jpg'}
        try:
            uri="http://{}:8080/requests/status.xml".format(config.ip)
            r = requests.get(url=uri,auth=HTTPBasicAuth(username="",password='maxai'))
            y = xmltodict.parse(r.content)
            x = y['root']['information']['category'][0]['info']
            filename = None
            
            for i in x:
                if i['@name'] =='title':
                    d['name']=i['#text']

                elif i['@name'] == 'artist':
                    d['artist'] = i['#text']
                
                elif i['@name'] == 'artwork_url':
                    d["artwork"] = i['#text']

                elif i['@name']=='filename':
                    filename = i['#text'].split(".")[0]

            if d['name'] == 'Offline':
                if filename:
                    d['name'] = filename
        except Exception as e: 
            a=1
        return d
class SongCover(MDBoxLayout):
    pass

class MaxxClient(MDApp):
    def cmd_executer(self):
        while True: 
            try:
                with open('cmd.txt','r') as cmd:
                    message = cmd.readline()
                cmd.close()
                task,msg = message.split("~")
                if task=="WEBBROWSER":
                    print(f"TASK: {message}")
                    with open('cmd.txt','w') as cmd:
                        cmd.write("")
                    cmd.close()
                    webbrowser.open(msg)
            except : continue

    def on_start(self):
        self.hsh="NONE"
        self.is_mute = False
        self.user_config= None
        with open('./config.json','r') as f:
            self.user_config = json.load(f)
        f.close()
        theme = self.user_config['theme']
        if theme == "Dark":
            self.root.get_screen('main').ids.darkmode_switch.active=True
        else:
            self.root.get_screen('main').ids.darkmode_switch.active=False
        self.theme_cls.theme_style=theme
        x=threading.Thread(target=self.cmd_executer,daemon=True)
        x.start()
        try:
            file = open('data.pickle',"rb")
            data =pickle.load(file)
            file.close()

            self.dev_name, self.ip, self.port = data
            self.connect_server()
        except Exception as e:
            print("EXCEPTION: {}".format(e))

    def on_stop(self):

        self.client.send("!DISCONNECT".encode(encoding))
        self.client.close()
        
        try:
            from jnius import autoclass
            service = autoclass("org.maxxai.maxxclient.ServiceMaxxservice")
            mActivity = autoclass("org.kivy.android.PythonActivity").mActivity
            service.stop(mActivity,"")
            
            print("service stoped")

        except Exception as e:
            print("SERVICE STOP : {}".format(e))

    def get_playlist(self):
        try:
            uri = "http://{}:4151/requests/playlist.xml".format(self.ip)
            r = requests.get(url=uri,auth=HTTPBasicAuth(username="",password='maxxai'))
            y = xmltodict.parse(r.content)
            data = y['node']['node'][0]['leaf']
            lst=[]

            for i in data:
                name = i['@name'].split(".")[0]
                d = {'name':name,'id':i['@id']}
                lst.append(d)

            return lst
        except: return None

    def build(self):
        self.theme_cls.theme_style="Light"
        app = Builder.load_file("app.kv")
        return app
    
    def change_theme(self):
        if self.root.get_screen('main').ids.darkmode_switch.active==True:
            self.theme_cls.theme_style="Dark"
            self.user_config['theme']="Dark"
        else:
            self.theme_cls.theme_style="Light"
            self.user_config['theme']="Light"

        with open("./config.json","w") as f:
            json.dump(self.user_config,f,indent=2)
        f.close()

    def switch_inside(self,screen):
        self.root.get_screen('main').ids.nav_drawer.set_state('close')
        self.root.get_screen('main').ids.inner_screen_manager.current=screen
    
    def disconnect(self, args):
        self.dialog.dismiss()
        if config.service == True:
            self.client.send("!DISCONNECT".encode(encoding))
            config.service = False
        print("disconnected")
        f = open("./data.pickle","wb")
        pickle.dump(obj=False,file=f)
        f.close()

        self.root.current  = "connect"

    def dismiss_dia(self, args):
        print("dismiss")
        self.dialog.dismiss()
        
    def logout(self):
        print("logging out")
        self.root.get_screen('main').ids.nav_drawer.set_state('close')
        self.dialog = MDDialog(text="Are you sure you want to logout",title="Logout", buttons=[
            MDFlatButton(text="No", on_release = self.dismiss_dia),
            MDFlatButton(text="Yes",
            on_release=self.disconnect),

            ])
        self.dialog.open()

    def send_msg(self):
        msg = self.root.get_screen('main').ids.msg_text.text
        if msg =="":
            return
        item = OneLineListItem(text=msg)
        self.root.get_screen('main').ids.msg_text.text = ""
        
        try:
            data = msg
            data = "MSG~"+data
            self.client.send(data.encode(encoding))
            self.root.get_screen('main').ids.msg_log.add_widget(item)
        except Exception as e:
            print("EXCEPTION: {}".format(e))
            self.client.close()
            self.client = None
            self.root.current = "connect"

    def media_control(self, msg):
        try:
            uri = "http://{}:8080/requests/status.xml?command={}".format(self.ip,msg)
            r = requests.get(url=uri,auth=HTTPBasicAuth(username="",password='maxai'))

            if r.status_code!=200: 
                print(r.content)

            self.update_playlist("")
        except:
            return

    def check_data(self):
        self.dialog = None
        name_valid = True
        ip_valid = True
        port_valid = True
        print("Checking data")
        device_name = self.root.get_screen('connect').ids.devicename.text
        ip = self.root.get_screen('connect').ids.ip.text
        port = self.root.get_screen('connect').ids.port.text
        self.symbols = '`~!@#$%^&*()_+-={[]}:;"\'<>,./?'
        numbers = '1234567890'
        ip=ip.strip()
        port = port.strip()

        if device_name=="" or device_name=="server":
            print("invalid")
            name_valid = False

        else:

            for i in self.symbols:
                if i in device_name:
                    name_valid = False
                    break
            for i in numbers:
                if i in device_name:
                    name_valid = False
                    break       

        if name_valid == False:
            if not self.dialog:
                self.dialog = MDDialog(text="Invalid Device Name",title="Error", buttons=[
                    MDFlatButton(text="OK",
                    on_release=self.clear_dev)
                    ])
                self.dialog.open()

        if ip=="":
            ip_valid = False

        else:
            for i in ip:
                
                if i.isalpha():
                    ip_valid = False
                    break
                elif i in self.symbols.replace(".",""):
                    ip_valid = False
                    break

        if ip_valid:
            ip_chck = ip.split(".")
            if len(ip_chck) != 4:
                ip_valid = False   

        if ip_valid == False:
            if not self.dialog:

                self.dialog = MDDialog(text="Invalid IP Address",title="Error", buttons=[
                    MDFlatButton(text="OK",
                    on_release=self.clear_ip)
                    ])
                self.dialog.open()

        if port =="":
            port_valid = False
        try:
            port = int(port)
        except:
            port_valid = False

        if port_valid == False:

            if not self.dialog:
                self.dialog = MDDialog(text="Invalid Port Number",title="Error", buttons=[
                    MDFlatButton(text="OK",
                    on_release=self.clear_port)
                    ])
                self.dialog.open()

        if name_valid and ip_valid and port_valid:
            print("valid")
            self.ip = ip
            self.port = port
            self.dev_name = device_name
            self.root.get_screen('connect').ids.devicename.text=""
            self.root.get_screen('connect').ids.ip.text=""
            self.root.get_screen('connect').ids.port.text=""
            
            self.connect_server()

    def clear(self,args):
        self.root.get_screen('connect').ids.devicename.text = ""
        self.root.get_screen('connect').ids.ip.text = ""
        self.root.get_screen('connect').ids.port.text = ""
        self.dialog.dismiss()

    def clear_dev(self, arg):
        self.root.get_screen('connect').ids.devicename.text = ""
        self.dialog.dismiss()

    def clear_ip(self, args):
        self.root.get_screen('connect').ids.ip.text = ""
        self.dialog.dismiss()

    def clear_port(self, args):
        self.root.get_screen('connect').ids.port.text = ""
        self.dialog.dismiss()

    def listen_conn(self):  
        print("Daemon listening")
        self.client.settimeout(10)
        while config.service:                                           
            try:
                client = self.client
                message = client.recv(buffer).decode(encoding)
                print(message)
                if message == '!DISCONNECT':
                    client.send("DISCONNECTED".encode(encoding))
                    print("disconnect funtion")
                    client.close()
                    config.client=None
                    config.service = False
                    exit()
                    
                elif message == '!ALIVE':
                    print("alive")
                    client.send("alive".encode(encoding))
                else:
                    print("checking for any other msg")
                    msg = message.split("~")
                    message = "FALSE"

                    print("before send msg " +message)
                    client.send(message.encode(encoding))
                    print("after send msg ")
            except Exception as e: 
                if "timed out" in "{}".format(e):
                    continue
                print("An error occured!")
                client.close()
                config.service=False
                break   

    def connect_server(self):
        print("connect server")
        config.ip = self.ip
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(10)
        print("created client obj")
        print(self.ip,self.port)
        try:
            f = open('hash.pickle','rb')
            self.hsh = pickle.load(f)
            print("HASH CONNECT : "+self.hsh)
            f.close()
        except Exception as e: 
            print(e)
            self.hsh = 'NONE'

        self.client.connect((self.ip,int(self.port)))
        print("connect to obj")
        print(self.ip,self.port)
        message = self.client.recv(buffer).decode(encoding)

        if message == 'NICKNAME':
            msg=self.dev_name+"~"+self.hsh
            self.client.send(msg.encode(encoding))
        self.client.settimeout(None)
        message = self.client.recv(buffer).decode(encoding)
        self.client.settimeout(10)

        print(message)
        if message=="CONNECTIONACCEPTED":
            hsh = self.client.recv(buffer).decode(encoding)
            print("HASH : {}".format(hsh))
            config.service = True
            config.client = self.client
            print(config.client)

            data = [self.dev_name,self.ip,self.port]
            file = open("./data.pickle","wb")
            pickle.dump(data,file=file)
            file.close()
            hash_file = open("./hash.pickle","wb")
            pickle.dump(hsh,hash_file)
            hash_file.close()
            try:
                print("before android import")
                from jnius import autoclass
                service = autoclass("org.maxxai.maxxclient.ServiceMaxxservice")
                mActivity = autoclass("org.kivy.android.PythonActivity").mActivity
                service.start(mActivity,"")
                
                print("service started")

            except Exception as e:
                print("service exception")
                print(e)
            


            x=threading.Thread(target=self.listen_conn,daemon=True)
            x.start()
            self.root.current="main"

        elif message=="!NAME":
            print("NAME ALREADY CHOSEN")

        else:
            if not self.dialog:

                self.dialog = MDDialog(
                    title="Connection Refused",
                    text="The connection has been declined by the server.",
                    buttons=[
                        MDFlatButton(
                            text="OK",
                            on_release=self.clear
                        ),
                    ]
                )
            self.dialog.open()

if __name__ == "__main__":
	MaxxClient().run()


