import socket
import pyodbc
import threading
import logging
import sys
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.config import Config
import pandas as pd


# class to build GUI for a popup window
class P(FloatLayout):
    pass


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    """ Adds selection and focus behaviour to the view. """
    selected_value = StringProperty('')
    btn_info = ListProperty(['Button 0 Text', 'Button 1 Text', 'Button 2 Text', 'Button 3 Text', 'Button 4 Text', 'Button 5 Text'])


class ConnectionList(RecycleView):
    rv_layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ConnectionList, self).__init__(**kwargs)
        self.data = [{'text': "Button " + str(x), 'id': str(x)} for x in range(6)]


class LoginWindow(Screen):
    pass


# Create a Socket ( connect two computers)
def create_socket():
    try:
        global host
        global port
        global s
        host = ""
        port = 9999
        s = socket.socket()

    except socket.error as msg:
        print("Socket creation error: " + str(msg))


def bind_socket():
    try:
        global host
        global port
        global s
        print("Binding the Port: " + str(port))

        s.bind((host, port))
        s.listen(5)

    except socket.error as msg:
        print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
        bind_socket()


# Establish connection with a client (socket must be listening)

def socket_accept():
    conn, address = s.accept()
    print("Connection has been established! |" + " IP " + address[0] + " | Port" + str(address[1]))
    send_commands(conn)
    conn.close()


# Send commands to client/victim or a friend
def send_commands(conn):
    while True:
        cmd = input()
        if cmd == 'quit':
            print("command quit: " + str(cmd))
            conn.close()
            s.close()
            sys.exit()
        if cmd == 'cd':
            print("command cd: " + str(cmd))
        if len(str.encode(cmd)) > 0:
            conn.send(str.encode(cmd))
            client_response = str(conn.recv(1024),"utf-8")
            print(client_response, end="")


class ServerWindow(Screen):
    create_socket()
    bind_socket()
    t1 = threading.Thread(target=socket_accept, daemon=True)
    t1.start()

# class for managing screens
class WindowManager(ScreenManager):
    pass


sm = WindowManager()


class MainApp(MDApp):
    conn = None
    cursor = None
    df = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        # kv file
        kv = Builder.load_file('windows.kv')

        # adding screens
        sm.add_widget(LoginWindow(name='login'))
        sm.add_widget(ServerWindow(name='server'))
        sm.current = 'login'
        return sm

    def disp_msg(self, name):
        menuscreen = self.root.get_screen('login')
        menuscreen.ids.msg_label.text = f'Sup {name}!'

    def read(self, conn, msg):
        #cursor = conn.cursor()
        sql = "select Description, " \
                        "LastSold, " \
                        "SubDescription1," \
                        "SubDescription2," \
                        "SubDescription3," \
                        "Price," \
                        "SalePrice," \
                        "Cost," \
                        "DepartmentID," \
                        "SaleStartDate," \
                        "SaleEndDate," \
                        "SupplierID" \
                        " from Item where ItemLookupCode = '" + str(msg) + "'"
        #detail = cursor.execute("select Description from Item where ItemLookupCode = '" + str(msg) + "'")
        self.df = pd.read_sql(sql, self.conn)
        return self.df
        #print(cursor)

    # function that displays the content
    def popFun(self):
        show = P()
        window = Popup(title="Please enter valid information?", content=show,
                       size_hint=(None, None), size=(300, 100))
        window.open()

    def rmshelper_server_connect(self):
        self.disp_msg("PyCharm Start")
        menuscreen = self.root.get_screen('login')
        if len(menuscreen.ids.server.text) and len(menuscreen.ids.dbname.text) and len(menuscreen.ids.password.text) != 0:
            try:
                self.conn = pyodbc.connect(
                    'DRIVER={ODBC Driver 18 for SQL Server};'
                    'SERVER=' + menuscreen.ids.server.text + ',1433;'
                    'DATABASE=' + menuscreen.ids.dbname.text + ';'
                    'UID=sa;'
                    'PWD=' + menuscreen.ids.password.text + ';'
                    'TrustServerCertificate=yes;'
                )
                #self.read(conn)
                sm.current = 'server'


            except pyodbc.Error as err:
                self.popFun()
                self.clear()
        else:
            self.popFun()

        self.disp_msg("PyCharm End")

        #read(conn)
        #self.root.ids.rmshelper_label.text = f'Sup {self.root.ids.server.text}!'


    def clear(self):
        menuscreen = self.root.get_screen('login')
        menuscreen.ids.rmshelper_label.text = "RMSHelper Server"
        menuscreen.ids.server.text = ""
        menuscreen.ids.dbname.text = ""
        menuscreen.ids.password.text = ""


    def exit(self):
        #return self.root_window.close()
        return sys.exit()


    def handle_message(self, msg):
        msg = msg.decode('utf-8')
        self.df = self.read(self.conn, str(msg))
        sm.get_screen('server').ids.msg_label.text = self.df.to_string()
        return self.df.to_string()


# driver function
if __name__ == "__main__":
    MainApp().run()