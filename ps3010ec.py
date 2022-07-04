#! /usr/bin/env python

import sys
import logging as l
import asyncio
import os
from async_tkinter_loop import async_mainloop
import tkinter as tk
from tkinter import ttk
from ttkwidgets import tooltips
import configparser
from PS3010EC_Modbus import PS3010EC_Modbus, PS3010EC_Exception
from PIL import Image, ImageTk
from SevenSegmentModule import SevenSegmentModule


class App(tk.Tk):
    """The root window for the application"""

    # Application variables

    # self.config
    # self.root_frame
    # self.polled_values
    # self.set_by_app
    # self.number_images = dict()
    # self.label_frame_images = dict()
    # self.label_status_images = dict()
    # self.label_images = dict()
    # self.button_images = dict()
    # self.radiobutton_images = dict()
    # self.checkbutton_images = dict()

    # self.frames={}  #Keys here are the sections of the interface e.g. 'U', 'I', etc.

    # # The following dictionary pattern is used for the 'U' and 'I' sections
    # self.frames['U' or 'I']['frame']
    # self.frames['U' or 'I']['display']
    # self.frames['U' or 'I']['reg_mode_banner']
    # self.frames['U' or 'I']['reg_mode_banner_text']

    # self.frames['RS']['frame']
    # self.frames['RS']['run_stop_button']

    # self.frames['SetU' or 'SetI']['frame']
    # self.frames['SetU' or 'SetI']['display']
    # self.frames['SetU' or 'SetI']['digits_up_buttons'][0-2]
    # self.frames['SetU' or 'SetI']['digits_down_buttons'][0-2]

    # self.frames['SetMode']['frame']
    # self.frames['SetMode']['mode_label']

    # self.frames['SetCmd']['frame']
    # self.frames['SetCmd']['off_before_change']
    # self.frames['SetCmd']['off_before_change_checkbutton']
    # self.frames['SetCmd']['on_after_change']
    # self.frames['SetCmd']['on_after_change_checkbutton']
    # self.frames['SetCmd']['apply_button']

    # self.frames['Config']['frame']
    # self.frames['Config']['subframes']= dict()   # Either 'serial' or 'network'
    # self.frames['Config']['comm_method_buttons]
    # self.frames['Config']['comm_method_text]
    # self.frames['Config']['comm_text_box']
    # self.frames['Config']['ipaddr_text_box']
    # self.frames['Config']['port_text_box']
    # self.frames['Config']['connect_button']
    # self.frames['Config']['quit_button']
    # self.frames['Config']['find_button']
    # self.frames['Config']['save_config_button']
    # self.frames['Config']['connection_status']

    # self.frames['Mem']['frame']
    # self.frames['Mem']['registers'][0-4]['U']              # Register 0 is the PS value
    # self.frames['Mem']['registers'][0-4]['U']['display']   # Registers 1-4 are local app registers
    # self.frames['Mem']['registers'][0-4]['I']
    # self.frames['Mem']['registers'][0-4]['I']['display']
    # self.frames['Mem']['registers'][0-4]['sto_button']
    # self.frames['Mem']['registers'][0-4]['rcl_button']

    def __init__(self, title, geometry, asyncQ):
        """ The application is for a Programmable Power Supply(PS) Control Interface
        for the Longwei LW-3010EC and similar

        The PS will switch between Constant Voltage (CV) and Constant Current (CC)
        regulation modes as well as Over Current Protection Mode

        The Present Voltage or Present Current frames will modify their background
        color and update a status display to indicate which mode the PS is in.

        If the Over Current Protection (OCP) trips the ouput will be disabled by the
        PS firwmare.  Since there is no Modbus registers for the OCP controls any
        OCP errors or setting must be done from the device interface

        The configuration file for communication and memory registers is at
        ~/.config/ps3010ec/config.ini
        """

        super().__init__()
        self.title(title)
        self.resizable(False, False)
        try:
            self.root_width, self.root_height = geometry.split('x')
            #print(f"self.rood_width: {self.root_width}, self.root_height: {self.root_height}")
        except ValueError as e:
            print(f"Geometry value could not be parsed.  geometry: {geometry}")
            sys.exit(1)

        try:
            self.config = configparser.ConfigParser()
            self.config_path = os.path.join(os.path.expanduser('~'),
                                            '.config/ps3010ec/config.ini')
            self.config.read(self.config_path)

        except configparser.Error as e:
            print(repr(e))
            print(e)
            sys.exit(1)

        # Attach the quit message to the Window Manager close icon
        self.protocol('WM_DELETE_WINDOW', self.send_appQuit_to_queue)

        # Colors used by the GUI and bitmaps
        # 'black'            #000000
        # 'chocolate1'       #ff7f24
        # 'darkorange4'      #8b4500
        # 'dim gray'         #696969
        # 'gray'             #bebebe
        # 'gray24'           #3d3d3d
        # 'gray90'           #e5e5e5
        # 'lemon chiffon'    #fffacd
        # 'light steel blue' #b0c4de
        # 'firebrick3'       #cd2626
        # 'seagreen1'        #54ff9f
        # 'steel blue'       #4682b4
        # 'steelblue2'       #5cacee
        # 'steelblue3'       #4f94cd
        # 'steelblue4'       #36648b
        # 'white'            #ffffff

        # Colors, Fonts, and Styles for the GUI
        self.dbg = 'chocolate1'  #Default background
        self.dfg = 'gray24'  #Default foreground
        self.sbg = 'darkorange4'  #Selected background
        self.sfg = 'lemon chiffon'  #Selected foreground

        self.ps_style = ttk.Style()

        self.ps_style.configure('TFrame', background='gray')

        self.ps_style.configure('Root.TFrame', background='dim gray')

        self.ps_style.configure('ActiveRegMode.TFrame',
                                background='steelblue3')
        self.ps_style.configure('ErrorRegMode.TFrame', background='firebrick3')
        self.ps_style.configure('SetByAppMode.TFrame',
                                background='steelblue2',
                                borderwidth=-1)
        self.ps_style.configure('SetByPSMode.TFrame',
                                background='dim gray',
                                borderwidth=-1)

        self.ps_style.configure('CommMethod.TFrame',
                                background='gray',
                                borderwidth=-1,
                                anchor='center',
                                stick='nsew')

        self.ps_style.configure('TLabel',
                                anchor='center',
                                sticky='nsew',
                                foreground=self.dfg,
                                background=self.dbg,
                                borderwidth=-1)
        self.ps_style.configure('FrameLabel.TLabel',
                                foreground='steel blue',
                                background='light steel blue',
                                borderwidth=-1)

        self.ps_style.configure('TButton',
                                anchor='nw',
                                sticky='nsew',
                                foreground=self.dfg,
                                background=self.dbg,
                                padding=0,
                                borderwidth=-1)
        self.ps_style.map('TButton', background=[('active', self.sbg)])
        self.ps_style.map('TButton', foreground=[('active', self.sfg)])

        self.ps_style.configure('TCheckbutton',
                                justify='center',
                                foreground=self.dfg,
                                background=self.dbg)

        self.ps_style.map('TCheckbutton', background=[('active', self.sbg)])
        self.ps_style.map('TCheckbutton', foreground=[('active', self.sfg)])

        self.ps_style.configure('CommMethod.TRadiobutton',
                                anchor='nw',
                                sticky='nsew',
                                foreground=self.dfg,
                                background=self.dbg,
                                padding=0,
                                margin=0,
                                borderwidth=-1,
                                highlightthickness=-1)
        self.ps_style.map('CommMethod.TRadiobutton',
                          background=[('active', self.sbg)])
        self.ps_style.map('CommMethod.TRadiobutton',
                          foreground=[('active', self.sfg)])

        self.ps_style.configure('TEntry',
                                foreground=self.dfg,
                                fieldbackground=self.dbg,
                                selectbackground=self.sbg,
                                selectforeground=self.sfg)

        # End Colors, Fonts, and Styles for the GUI

        self.root_frame = ttk.Frame(self,
                                    width=self.root_width,
                                    height=self.root_height,
                                    style='Root.TFrame')
        self.root_frame.grid(sticky='nsew')

        # AsyncIO Q
        self.asyncQ = asyncQ
        self.holdingQ = []

        self.set_by_app = False
        # When False the SetU and SetI displays won't show the displayed value
        # even if the PS controls change the settings.  This allows the SetU
        # and SetI controls on the Application to be independant of the PS.
        # To reset to True (and display # the set values from the PS restore
        # from the "PS" register in the Memory frame

        # Hold the values polled from the power supply
        self.polled_values = {}
        self.polled_values['U'] = {}
        self.polled_values['U']['last_polled_value'] = 0
        self.polled_values['I'] = {}
        self.polled_values['I']['last_polled_value'] = 0
        self.polled_values['SetU'] = {}
        self.polled_values['SetU']['last_polled_value'] = 0
        self.polled_values['SetI'] = {}
        self.polled_values['SetI']['last_polled_value'] = 0
        self.polled_values['RunStop'] = {}
        self.polled_values['RunStop'][
            'last_polled_value'] = 0xFF  # Invalid value, forces update on GUI startup
        self.polled_values['RegMode'] = {}
        self.polled_values['RegMode'][
            'last_polled_value'] = 0xFF  # Invalid value, forces update on GUI startup

        # bitmap images of digits passed to the 7SegmentDisplay objects
        self.number_images = dict()
        for size in ('l', 'm', 's'):
            self.number_images[size] = dict()
            for ordinal in ('d', 'nd'):
                self.number_images[size][ordinal] = list()
                for i in range(0, 10):
                    self.number_images[size][ordinal].append(
                        ImageTk.PhotoImage(
                            file=f"assets/digit-{i}-{ordinal}-{size}.png"))

        # GUI bitmaps
        self.label_frame_images = dict()
        self.label_frame_images['voltage'] = ImageTk.PhotoImage(
            file=f"assets/label-voltage.png")
        self.label_frame_images['current'] = ImageTk.PhotoImage(
            file=f"assets/label-current.png")
        self.label_frame_images['output'] = ImageTk.PhotoImage(
            file=f"assets/label-output.png")
        self.label_frame_images['setvoltage'] = ImageTk.PhotoImage(
            file=f"assets/label-setvoltage.png")
        self.label_frame_images['setcurrent'] = ImageTk.PhotoImage(
            file=f"assets/label-setcurrent.png")
        self.label_frame_images['set'] = ImageTk.PhotoImage(
            file=f"assets/label-set.png")
        self.label_frame_images['set_mode'] = ImageTk.PhotoImage(
            file=f"assets/label-set_mode.png")
        self.label_frame_images['set_mode_blank'] = ImageTk.PhotoImage(
            file=f"assets/label-set_mode-blank.png")
        self.label_frame_images['configuration'] = ImageTk.PhotoImage(
            file=f"assets/label-configuration.png")
        self.label_frame_images['memory'] = ImageTk.PhotoImage(
            file=f"assets/label-memory.png")

        self.label_status_images = dict()
        self.label_status_images['voltage-limited'] = ImageTk.PhotoImage(
            file=f"assets/status-voltagelimited.png")
        self.label_status_images['current-limited'] = ImageTk.PhotoImage(
            file=f"assets/status-currentlimited.png")
        self.label_status_images['hide-limited'] = ImageTk.PhotoImage(
            file=f"assets/status-hidelimited.png")
        self.label_status_images['ocp-u'] = ImageTk.PhotoImage(
            file=f"assets/status-ocp-u.png")
        self.label_status_images['ocp-i'] = ImageTk.PhotoImage(
            file=f"assets/status-ocp-i.png")
        self.label_status_images['outputoff'] = ImageTk.PhotoImage(
            file=f"assets/status-outputoff.png")
        self.label_status_images['outputon'] = ImageTk.PhotoImage(
            file=f"assets/status-outputon.png")

        self.label_images = dict()
        self.label_images['comm'] = ImageTk.PhotoImage(
            file=f"assets/label-comm.png")
        self.label_images['ipaddr'] = ImageTk.PhotoImage(
            file=f"assets/label-ipaddr.png")
        self.label_images['port'] = ImageTk.PhotoImage(
            file=f"assets/label-port.png")
        self.label_images['v'] = ImageTk.PhotoImage(file=f"assets/label-v.png")
        self.label_images['i'] = ImageTk.PhotoImage(file=f"assets/label-i.png")
        self.label_images['ps'] = ImageTk.PhotoImage(
            file=f"assets/label-ps.png")
        self.label_images['m1'] = ImageTk.PhotoImage(
            file=f"assets/label-m1.png")
        self.label_images['m2'] = ImageTk.PhotoImage(
            file=f"assets/label-m2.png")
        self.label_images['m3'] = ImageTk.PhotoImage(
            file=f"assets/label-m3.png")
        self.label_images['m4'] = ImageTk.PhotoImage(
            file=f"assets/label-m4.png")

        self.button_images = dict()
        self.button_images['arrow-up'] = ImageTk.PhotoImage(
            file=f"assets/button-arrow-up.png")
        self.button_images['arrow-down'] = ImageTk.PhotoImage(
            file=f"assets/button-arrow-down.png")
        self.button_images['mem-store'] = ImageTk.PhotoImage(
            file=f"assets/button-store.png")
        self.button_images['mem-recall'] = ImageTk.PhotoImage(
            file=f"assets/button-recall.png")
        self.button_images['mem-recall-setfromapp'] = ImageTk.PhotoImage(
            file=f"assets/button-recall-setfromapp.png")
        self.button_images['button-conn'] = ImageTk.PhotoImage(
            file=f"assets/button-conn.png")
        self.button_images['button-disconn'] = ImageTk.PhotoImage(
            file=f"assets/button-disconn.png")
        self.button_images['button-save'] = ImageTk.PhotoImage(
            file=f"assets/button-save.png")
        self.button_images['button-quit'] = ImageTk.PhotoImage(
            file=f"assets/button-quit.png")
        self.button_images['button-find'] = ImageTk.PhotoImage(
            file=f"assets/button-find.png")
        self.button_images['button-apply'] = ImageTk.PhotoImage(
            file=f"assets/button-apply.png")
        self.button_images['button-run'] = ImageTk.PhotoImage(
            file=f"assets/button-run.png")
        self.button_images['button-stop'] = ImageTk.PhotoImage(
            file=f"assets/button-stop.png")

        self.radiobutton_images = dict()
        self.radiobutton_images['serial'] = ImageTk.PhotoImage(
            file=f"assets/radiobutton-serial.png")
        self.radiobutton_images['network'] = ImageTk.PhotoImage(
            file=f"assets/radiobutton-network.png")

        self.checkbutton_images = dict()
        self.checkbutton_images['off-before-change'] = ImageTk.PhotoImage(
            file=f"assets/checkbutton-outputoffbeforechange.png")
        self.checkbutton_images['on-after-change'] = ImageTk.PhotoImage(
            file=f"assets/checkbutton-outputonafterchange.png")

        # Root dictionary for all the elements of the visible frames and widgets
        self.frames = {}

        # Create and place the 9 major frames for the App
        # The names of the sections come from the ModBus programming guide for the PS
        # Except for 'SetMode' which is necessary to allow the GUI independant control
        # Of the SetU and SetI displays.
        self.frames['U'] = {}
        self.frames['U']['frame'] = ttk.Frame(self.root_frame)
        self.frames['U']['frame'].place(width=260, height=150, x=35, y=25)
        self.frames['I'] = {}
        self.frames['I']['frame'] = ttk.Frame(self.root_frame)
        self.frames['I']['frame'].place(width=260, height=150, x=350, y=25)
        self.frames['RS'] = {}
        self.frames['RS']['frame'] = ttk.Frame(self.root_frame)
        self.frames['RS']['frame'].place(width=135, height=150, x=630, y=25)
        self.frames['SetU'] = {}
        self.frames['SetU']['frame'] = ttk.Frame(self.root_frame)
        self.frames['SetU']['frame'].place(width=203, height=170, x=66, y=190)
        self.frames['SetI'] = {}
        self.frames['SetI']['frame'] = ttk.Frame(self.root_frame)
        self.frames['SetI']['frame'].place(width=203, height=170, x=381, y=190)
        self.frames['SetMode'] = {}
        self.frames['SetMode']['frame'] = ttk.Frame(self.root_frame,
                                                    style='SetByPSMode.TFrame')
        self.frames['SetMode']['frame'].place(width=112,
                                              height=80,
                                              x=269,
                                              y=230)
        self.frames['SetCmd'] = {}
        self.frames['SetCmd']['frame'] = ttk.Frame(self.root_frame)
        self.frames['SetCmd']['frame'].place(width=135,
                                             height=170,
                                             x=630,
                                             y=190)
        self.frames['Config'] = {}
        self.frames['Config']['frame'] = ttk.Frame(self.root_frame)
        self.frames['Config']['frame'].place(width=260,
                                             height=200,
                                             x=35,
                                             y=375)

        self.frames['Mem'] = {}
        self.frames['Mem']['frame'] = ttk.Frame(self.root_frame)
        self.frames['Mem']['frame'].place(width=415, height=200, x=350, y=375)

        ####   ===============================================================

        # The 'U' frame shows the voltage currently being delivered by the PS
        # shorthand for clarity of code
        pt = self.frames['U']
        fpt = pt['frame']

        ttk.Label(fpt,
                  image=self.label_frame_images['voltage'],
                  style='FrameLabel.TLabel').place(anchor='n', x=130, y=8)

        # 'U' Display
        pt['display'] = SevenSegmentModule(
            fpt,
            height=80,
            width=56,
            images_dp=self.number_images['l']['d'],
            images_ndp=self.number_images['l']['nd'],
            max_value=PS3010EC_Modbus.MAX_U_RAW)
        pt['display'].place(anchor='center', x=130, y=75)

        pt['subframes'] = {}

        pt['subframes']['voltage-limited'] = ttk.Frame(fpt,
                                                       width=244,
                                                       height=18)
        ttk.Label(pt['subframes']['voltage-limited'],
                  image=self.label_status_images['voltage-limited']).pack()
        pt['subframes']['voltage-limited'].place(anchor='s', x=130, y=140)

        pt['subframes']['hide-limited'] = ttk.Frame(fpt, width=244, height=18)
        ttk.Label(pt['subframes']['hide-limited'],
                  image=self.label_status_images['hide-limited']).pack()
        pt['subframes']['hide-limited'].place(anchor='s', x=130, y=140)

        pt['subframes']['ocp'] = ttk.Frame(fpt, width=244, height=18)
        ttk.Label(pt['subframes']['ocp'],
                  image=self.label_status_images['ocp-u']).pack()
        pt['subframes']['ocp'].place(anchor='s', x=130, y=140)

        ####   ===============================================================

        # The 'I' frame shows the current presently being delivered by the PS
        # shorthand for clarity of code
        pt = self.frames['I']
        fpt = pt['frame']

        ttk.Label(fpt,
                  image=self.label_frame_images['current'],
                  style='FrameLabel.TLabel').place(anchor='n', x=130, y=8)

        # 'I' Display
        pt['display'] = SevenSegmentModule(
            fpt,
            height=80,
            width=56,
            images_dp=self.number_images['l']['d'],
            images_ndp=self.number_images['l']['nd'],
            max_value=PS3010EC_Modbus.MAX_I_RAW)
        pt['display'].place(anchor='center', x=130, y=75)

        pt['subframes'] = {}

        pt['subframes']['current-limited'] = ttk.Frame(fpt,
                                                       width=244,
                                                       height=18)
        ttk.Label(pt['subframes']['current-limited'],
                  image=self.label_status_images['current-limited']).pack()
        pt['subframes']['current-limited'].place(anchor='s', x=130, y=140)

        pt['subframes']['hide-limited'] = ttk.Frame(fpt, width=244, height=18)
        ttk.Label(pt['subframes']['hide-limited'],
                  image=self.label_status_images['hide-limited']).pack()
        pt['subframes']['hide-limited'].place(anchor='s', x=130, y=140)

        pt['subframes']['ocp'] = ttk.Frame(fpt, width=244, height=18)
        ttk.Label(pt['subframes']['ocp'],
                  image=self.label_status_images['ocp-i']).pack()
        pt['subframes']['ocp'].place(anchor='s', x=130, y=140)

        ####   ===============================================================

        # The Run/Stop (aka RunStop or RS) frame provides the controls for turning the PS output on/off
        # shorthand for clarity of code
        pt = self.frames['RS']
        fpt = pt['frame']

        ttk.Label(fpt,
                  image=self.label_frame_images['output'],
                  style='FrameLabel.TLabel').place(anchor='n', x=67, y=10)

        pt['run_stop_button'] = ttk.Button(
            fpt,
            image=self.button_images['button-run'],
            command=self.send_toggleRS_to_queue)

        pt['run_stop_button'].place(anchor='center',
                                    x=67,
                                    y=75,
                                    width=96,
                                    height=38)

        pt['subframes'] = {}

        pt['subframes']['outputoff'] = ttk.Frame(fpt, width=100, height=20)
        pt['subframes']['outputoff'].place(anchor='s', x=67, y=140)
        ttk.Label(pt['subframes']['outputoff'],
                  image=self.label_status_images['outputoff']).pack()

        pt['subframes']['outputon'] = ttk.Frame(fpt, width=100, height=20)
        pt['subframes']['outputon'].place(anchor='s', x=67, y=140)
        ttk.Label(pt['subframes']['outputon'],
                  image=self.label_status_images['outputon']).pack()

        ####   ===============================================================

        # The 'SetU' frame shows the present Voltage Limit set point

        # shorthand for clarity of code
        pt = self.frames['SetU']
        fpt = pt['frame']

        ttk.Label(fpt,
                  image=self.label_frame_images['setvoltage'],
                  style='FrameLabel.TLabel').pack(side='top', pady=8)

        # 'SetU' Display
        pt['display'] = SevenSegmentModule(
            fpt,
            height=58,
            width=40,
            images_dp=self.number_images['m']['d'],
            images_ndp=self.number_images['m']['nd'],
            max_value=PS3010EC_Modbus.MAX_U_RAW)
        pt['display'].place(anchor='center', x=102, y=70)

        # 3 Up Buttons display for 'SetU'
        pt['digits_up_buttons'] = []
        # Button for ones position
        pt['digits_up_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-up'],
                       command=self.inc_setu_by_one))
        pt['digits_up_buttons'][-1].place(x=82,
                                          y=120,
                                          width=32,
                                          height=22,
                                          anchor='center')
        # Button for tenths
        pt['digits_up_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-up'],
                       command=self.inc_setu_by_tenth))
        pt['digits_up_buttons'][-1].place(x=122,
                                          y=120,
                                          width=32,
                                          height=22,
                                          anchor='center')
        # Button for hundreths
        pt['digits_up_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-up'],
                       command=self.inc_setu_by_hundreth))
        pt['digits_up_buttons'][-1].place(x=162,
                                          y=120,
                                          width=32,
                                          height=22,
                                          anchor='center')

        # 3 Down Buttons display for 'SetU'
        pt['digits_down_buttons'] = []
        # Button for ones position
        pt['digits_down_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-down'],
                       command=self.dec_setu_by_one))
        pt['digits_down_buttons'][-1].place(x=82,
                                            y=150,
                                            width=32,
                                            height=22,
                                            anchor='center')
        # Button for tenths
        pt['digits_down_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-down'],
                       command=self.dec_setu_by_tenth))
        pt['digits_down_buttons'][-1].place(x=122,
                                            y=150,
                                            width=32,
                                            height=22,
                                            anchor='center')
        # Button for hundreths
        pt['digits_down_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-down'],
                       command=self.dec_setu_by_hundreth))
        pt['digits_down_buttons'][-1].place(x=162,
                                            y=150,
                                            width=32,
                                            height=22,
                                            anchor='center')

        ####   ===============================================================

        # The 'SetI' frame shows the present Current Limit set point
        # shorthand for clarity of code
        pt = self.frames['SetI']
        fpt = pt['frame']

        ttk.Label(fpt,
                  image=self.label_frame_images['setcurrent'],
                  style='FrameLabel.TLabel').pack(side='top', pady=8)

        # 'SetI' Display
        pt['display'] = SevenSegmentModule(
            fpt,
            height=58,
            width=40,
            images_dp=self.number_images['m']['d'],
            images_ndp=self.number_images['m']['nd'],
            max_value=PS3010EC_Modbus.MAX_U_RAW)
        pt['display'].place(anchor='center', x=102, y=70)

        # 3 Up Buttons display for 'SetI'
        pt['digits_up_buttons'] = []
        # Button for ones position
        pt['digits_up_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-up'],
                       command=self.inc_seti_by_one))
        pt['digits_up_buttons'][-1].place(x=82,
                                          y=120,
                                          width=32,
                                          height=22,
                                          anchor='center')
        # Button for tenths
        pt['digits_up_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-up'],
                       command=self.inc_seti_by_tenth))
        pt['digits_up_buttons'][-1].place(x=122,
                                          y=120,
                                          width=32,
                                          height=22,
                                          anchor='center')
        # Button for hundreths
        pt['digits_up_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-up'],
                       command=self.inc_seti_by_hundreth))
        pt['digits_up_buttons'][-1].place(x=162,
                                          y=120,
                                          width=32,
                                          height=22,
                                          anchor='center')

        # 3 Down Buttons display for 'SetI'
        pt['digits_down_buttons'] = []
        # Button for ones position
        pt['digits_down_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-down'],
                       command=self.dec_seti_by_one))
        pt['digits_down_buttons'][-1].place(x=82,
                                            y=150,
                                            width=32,
                                            height=22,
                                            anchor='center')
        # Button for tenths
        pt['digits_down_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-down'],
                       command=self.dec_seti_by_tenth))
        pt['digits_down_buttons'][-1].place(x=122,
                                            y=150,
                                            width=32,
                                            height=22,
                                            anchor='center')
        # Button for hundreths
        pt['digits_down_buttons'].append(
            ttk.Button(fpt,
                       image=self.button_images['arrow-down'],
                       command=self.dec_seti_by_hundreth))
        pt['digits_down_buttons'][-1].place(x=162,
                                            y=150,
                                            width=32,
                                            height=22,
                                            anchor='center')

        ####   ===============================================================
        # SetMode frame contains the label widgets that will appear when the
        # SetU and SetI frames are reflecting local application values and
        # are not being read from the PS
        # See comments for self.set_by_app Boolean

        pt = self.frames['SetMode']
        fpt = pt['frame']

        pt['subframes'] = {}

        pt['subframes']['app_mode'] = ttk.Frame(fpt,
                                                width=112,
                                                height=80,
                                                style='SetByAppMode.TFrame')
        pt['subframes']['app_mode'].place(x=7, y=0)
        pt['notice'] = ttk.Label(pt['subframes']['app_mode'],
                                 image=self.label_frame_images['set_mode'])
        pt['notice'].pack()

        pt['subframes']['ps_mode'] = ttk.Frame(fpt,
                                               width=112,
                                               height=80,
                                               style='SetByPSMode.TFrame')
        pt['subframes']['ps_mode'].place(x=7, y=0)
        pt['notice'] = ttk.Label(
            pt['subframes']['ps_mode'],
            image=self.label_frame_images['set_mode_blank'])
        pt['notice'].pack()

        ####   ===============================================================
        # SetCmd frame contains the controls for pushing the values of SetU and SetI to
        # be the active U and I for the power supply.

        pt = self.frames['SetCmd']
        fpt = pt['frame']

        ttk.Label(fpt,
                  image=self.label_frame_images['set'],
                  style='FrameLabel.TLabel').place(anchor='n', x=68, y=8)

        pt['off_before_change'] = tk.BooleanVar()
        try:
            self.config['set']
            pt['off_before_change'].set(self.config['set'].get(
                'output_off_before_change', False))
        except KeyError:
            pt['off_before_change'].set(False)

        pt['off_before_change_checkbutton'] = ttk.Checkbutton(
            fpt,
            image=self.checkbutton_images['off-before-change'],
            variable=pt['off_before_change'])
        pt['off_before_change_checkbutton'].place(anchor='n',
                                                  x=68,
                                                  y=40,
                                                  width=110,
                                                  height=35)

        pt['on_after_change'] = tk.BooleanVar()
        try:
            self.config['set']
            pt['on_after_change'].set(self.config['set'].get(
                'output_on_after_change', False))
        except KeyError:
            pt['on_after_change'].set(False)

        pt['on_after_change_checkbutton'] = ttk.Checkbutton(
            fpt,
            image=self.checkbutton_images['on-after-change'],
            variable=pt['on_after_change'])
        pt['on_after_change_checkbutton'].place(anchor='n',
                                                x=68,
                                                y=85,
                                                width=110,
                                                height=35)
        pt['apply_button'] = ttk.Button(
            fpt,
            image=self.button_images['button-apply'],
            command=self.send_applySet_to_queue)
        pt['apply_button'].place(anchor='s', x=68, y=160, width=60, height=30)

        ####   ===============================================================

        # Config Frame

        # The configuration frame has multiple communication methods ('serial' and 'network')
        # but only 'serial' works with the the PS3010EC as shipped by Longwei
        # Comment out the button place() calls to show in GUI

        pt = self.frames['Config']
        fpt = pt['frame']

        # pt['connection_status'] = True

        # Place the frame label
        ttk.Label(fpt,
                  image=self.label_frame_images['configuration'],
                  style='FrameLabel.TLabel').place(x=130,
                                                   y=19,
                                                   anchor='center')

        ttk.Label(fpt,
                  image=self.radiobutton_images['serial'],
                  style='MemoryLabel.TLabel').place(x=12, y=50, anchor='w')

        pt['comm_method_text'] = tk.StringVar()
        pt['comm_method_text'].set('Serial')
        pt['comm_method_buttons'] = []
        for image, value, x in ((self.radiobutton_images['serial'], 'Serial',
                                 52), (self.radiobutton_images['network'],
                                       'Network', 208)):
            pt['comm_method_buttons'].append(
                ttk.Radiobutton(fpt,
                                image=image,
                                value=value,
                                variable=pt['comm_method_text'],
                                style='CommMethod.TRadiobutton',
                                command=self.raise_command_method_frame))
        #     pt['comm_method_buttons'][-1].place(x=x,
        #                                         y=50,
        #                                         anchor='center',
        #                                         width=76,
        #                                         height=18)

        # create subframes for different comm methods
        #    These frame will be swapped in and out depending on the button selection
        pt['subframes'] = {}
        for method in ('serial', 'network'):
            pt['subframes'][method] = ttk.Frame(fpt,
                                                width=234,
                                                height=50,
                                                style='CommMethod.TFrame')
            pt['subframes'][method].place(x=130, y=95, anchor='center')

        self.raise_command_method_frame(
        )  # Make the serial frame the default shown

        ttk.Label(pt['subframes']['serial'],
                  image=self.label_images['comm'],
                  style='FrameLabel.TLabel').place(x=0, y=10, anchor='w')
        pt['comm_text_box'] = ttk.Entry(pt['subframes']['serial'], width=24)
        pt['comm_text_box'].place(x=234, y=10, anchor='e')
        try:
            pt['comm_text_box'].insert(
                tk.INSERT,
                self.config['communication'].get('comm', '/dev/ttyUSB0'))
        except KeyError:
            pt['comm_text_box'].insert(tk.INSERT, '/dev/ttyUSB0')

        ttk.Label(pt['subframes']['network'],
                  image=self.label_images['ipaddr'],
                  style='FrameLabel.TLabel').place(x=0, y=10, anchor='w')
        pt['ipaddr_text_box'] = ttk.Entry(pt['subframes']['network'], width=24)
        pt['ipaddr_text_box'].place(x=234, y=10, anchor='e')
        pt['ipaddr_text_box'].insert(tk.INSERT, '127.0.0.1')

        ttk.Label(pt['subframes']['network'],
                  image=self.label_images['port'],
                  style='FrameLabel.TLabel').place(x=0, y=40, anchor='w')
        pt['port_text_box'] = ttk.Entry(pt['subframes']['network'], width=24)
        pt['port_text_box'].place(x=234, y=40, anchor='e')
        pt['port_text_box'].insert(tk.INSERT, '502')

        # pt['connect_button'] = ttk.Button(
        #     fpt,
        #     image=self.button_images['button-disconn'],
        #     command=self.update_connection_status_display)
        # pt['connect_button'].place(x=248,
        #                            y=140,
        #                            height=30,
        #                            width=60,
        #                            anchor='e')

        pt['quit_button'] = ttk.Button(fpt,
                                       image=self.button_images['button-quit'],
                                       command=self.send_appQuit_to_queue)
        pt['quit_button'].place(x=10, y=175, height=30, width=60, anchor='w')

        pt['save_config_button'] = ttk.Button(
            fpt,
            image=self.button_images['button-save'],
            command=self.update_and_write_config_file)
        pt['save_config_button'].place(x=248,
                                       y=175,
                                       height=30,
                                       width=60,
                                       anchor='e')

        # pt['find_button'] = ttk.Button(fpt,
        #                                image=self.button_images['button-find'],
        #                                command=lambda: self.root_frame.quit())
        # pt['find_button'].place(x=130,
        #                         y=175,
        #                         height=30,
        #                         width=60,
        #                         anchor='center')

        ####   ===============================================================

        # Memory Registers Frame
        pt = self.frames['Mem']
        fpt = pt['frame']
        pt['registers'] = []
        rpt = pt['registers']

        # Fixed labels in frame
        ttk.Label(fpt,
                  image=self.label_frame_images['memory'],
                  style='FrameLabel.TLabel').place(x=206,
                                                   y=19,
                                                   anchor='center')

        ttk.Label(fpt,
                  image=self.label_images['v'],
                  style='MemoryLabel.TLabel').place(x=22,
                                                    y=80,
                                                    width=15,
                                                    anchor='center')
        ttk.Label(fpt,
                  image=self.label_images['i'],
                  style='MemoryLabel.TLabel').place(x=22,
                                                    y=110,
                                                    width=15,
                                                    anchor='center')

        # Create the memories columns.
        # Tuple contains index and frame relative pixel X location
        for i, x in ((0, 62), (1, 135), (2, 208), (3, 281), (4, 354)):
            # Place the memory number label ("PS" and 1-4)
            if i == 0:
                ttk.Label(fpt,
                          image=self.label_images['ps'],
                          style='MemoryLabel.TLabel').place(x=x,
                                                            y=50,
                                                            anchor='center')
            if i >= 1:
                ttk.Label(fpt,
                          image=self.label_images[f'm{i}'],
                          style='FrameLabel.TLabel').place(x=x,
                                                           y=50,
                                                           anchor='center')

            rpt.append(dict())  # Dictionary under each 'registers' instance

            # Memory register 'U' value
            rpt[-1]['U'] = {}
            rpt[-1]['U']['display'] = SevenSegmentModule(
                fpt,
                height=20,
                width=14,
                images_dp=self.number_images['s']['d'],
                images_ndp=self.number_images['s']['nd'],
                max_value=PS3010EC_Modbus.MAX_U_RAW)
            rpt[-1]['U']['display'].place(anchor='center', x=x, y=80)

            # Memory register 'I' value
            rpt[-1]['I'] = {}
            rpt[-1]['I']['display'] = SevenSegmentModule(
                fpt,
                height=20,
                width=14,
                images_dp=self.number_images['s']['d'],
                images_ndp=self.number_images['s']['nd'],
                max_value=PS3010EC_Modbus.MAX_I_RAW)
            rpt[-1]['I']['display'].place(anchor='center', x=x, y=110)

            # if this is a configurable memory register add the value from the config file
            if i >= 1:
                try:
                    rpt[-1]['U']['display'].value = int(
                        self.config['memory_registers'].get(f"memory_{i}_u"))
                    rpt[-1]['I']['display'].value = int(
                        self.config['memory_registers'].get(f"memory_{i}_i"))
                except KeyError:
                    pass

            # Recall Button from memory to Set Windows
            if i >= 1:
                rpt[-1]['rcl_button'] = ttk.Button(
                    fpt,
                    image=self.button_images['mem-recall'],
                    tooltip="Recall memory values to Set Windows",
                    command=eval(f"self.memRecall{i}"))
                rpt[-1]['rcl_button'].place(x=x,
                                            y=140,
                                            width=40,
                                            height=20,
                                            anchor='center')
            elif i == 0:
                rpt[-1]['rcl_button'] = ttk.Button(
                    fpt,
                    image=self.button_images['mem-recall'],
                    tooltip=
                    "Recall PS settings to Set Windows and end set_by_app mode",
                    command=eval(f"self.memRecall{i}"))
                rpt[-1]['rcl_button'].place(x=x,
                                            y=140,
                                            width=40,
                                            height=20,
                                            anchor='center')

            # Store Button to memory from Set Windows
            if i >= 1:
                rpt[-1]['sto_button'] = ttk.Button(
                    fpt,
                    image=self.button_images['mem-store'],
                    tooltip="Store values from Set Windows to memory",
                    command=eval(f"self.memStore{i}"))
                rpt[-1]['sto_button'].place(x=x,
                                            y=170,
                                            width=40,
                                            height=20,
                                            anchor='center')

####   ===============================================================
####   All Frames Completed

    def update_last_polled_value(self, polled_values):
        """Update the GUI frames with the last polled values supplied"""

        SetU = polled_values[0]
        SetI = polled_values[1]
        U = polled_values[2]
        I = polled_values[3]
        RunStop = polled_values[4]
        RegMode = polled_values[5]

        if RegMode != self.polled_values['RegMode']['last_polled_value']:
            self.polled_values['RegMode']['last_polled_value'] = RegMode
            self.set_regulation_mode(RegMode)

        if U != self.polled_values['U']['last_polled_value']:
            self.polled_values['U']['last_polled_value'] = U
            self.frames['U']['display'].value = U

        if I != self.polled_values['I']['last_polled_value']:
            self.polled_values['I']['last_polled_value'] = I
            self.frames['I']['display'].value = I

        # Only update the display from the polled values if not in local set mode
        if self.set_by_app != True:
            if SetU != self.polled_values['SetU']['last_polled_value']:
                self.polled_values['SetU']['last_polled_value'] = SetU
                self.frames['SetU']['display'].value = SetU

            if SetI != self.polled_values['SetI']['last_polled_value']:
                self.polled_values['SetI']['last_polled_value'] = SetI
                self.frames['SetI']['display'].value = SetI

        # "PS" memory register always displays polled value
        self.frames['Mem']['registers'][0]['U']['display'].value = SetU
        self.frames['Mem']['registers'][0]['I']['display'].value = SetI

        if RegMode != self.polled_values['RunStop']['last_polled_value']:
            self.polled_values['RunStop']['last_polled_value'] = RunStop
            self.update_runstop_display()

    def update_runstop_display(self):
        "Update the runstop icons and power output status strings"
        if self.polled_values['RunStop']['last_polled_value']:
            self.frames['RS']['run_stop_button'].configure(
                image=self.button_images['button-stop'])
            self.frames['RS']['subframes']['outputon'].tkraise()
        else:
            self.frames['RS']['run_stop_button'].configure(
                image=self.button_images['button-run'])
            self.frames['RS']['subframes']['outputoff'].tkraise()

    def update_connection_status_display(self):
        "Update the connect/disconnect button display"
        self.frames['Config']['connection_status'] = not (
            self.frames['Config']['connection_status'])
        if self.frames['Config']['connection_status']:
            self.frames['Config']['connect_button'].configure(
                image=self.button_images['button-disconn'])
        else:
            self.frames['Config']['connect_button'].configure(
                image=self.button_images['button-conn'])

    def set_set_by_app(self, set_by_app):
        "Sets the set_by_app status strings and colors of SetU and SetI frames"

        self.set_by_app = set_by_app

        if self.set_by_app == True:
            self.frames['SetU']['frame'].config(style='SetByAppMode.TFrame')
            self.frames['SetI']['frame'].config(style='SetByAppMode.TFrame')
            self.frames['SetMode']['subframes']['app_mode'].tkraise()
            self.frames['Mem']['registers'][0]['rcl_button'].configure(
                image=self.button_images['mem-recall-setfromapp'])

        if self.set_by_app == False:
            self.frames['SetU']['frame'].config(style='.TFrame')
            self.frames['SetI']['frame'].config(style='.TFrame')
            self.frames['SetMode']['subframes']['ps_mode'].tkraise()
            self.frames['Mem']['registers'][0]['rcl_button'].configure(
                image=self.button_images['mem-recall'])

    def set_regulation_mode(self, RegMode):
        "Raise the regulation mode status images and set colors of U and I frames"

        #print(f"in set_regulation_mode().  RegMode: {RegMode}")

        # Constant Current Mode
        if RegMode == PS3010EC_Modbus.REGULATION_MODE_CURRENT:
            self.frames['I']['frame'].config(style='ActiveRegMode.TFrame')
            self.frames['I']['subframes']['current-limited'].tkraise()
            self.frames['U']['frame'].config(style='TFrame')
            self.frames['U']['subframes']['hide-limited'].tkraise()

        # Constant Voltage Mode
        if RegMode == PS3010EC_Modbus.REGULATION_MODE_VOLTAGE:
            self.frames['U']['frame'].config(style='ActiveRegMode.TFrame')
            self.frames['U']['subframes']['voltage-limited'].tkraise()
            self.frames['I']['frame'].config(style='TFrame')
            self.frames['I']['subframes']['hide-limited'].tkraise()

        # Overcurrent Protection Active
        if RegMode == PS3010EC_Modbus.REGULATION_MODE_OVERCURRENT_PROTECTION:
            self.frames['I']['frame'].config(style='ErrorRegMode.TFrame')
            self.frames['I']['subframes']['ocp'].tkraise()
            self.frames['U']['frame'].config(style='ErrorRegMode.TFrame')
            self.frames['U']['subframes']['ocp'].tkraise()

    def pop_next_holdingQ(self):
        if len(self.holdingQ):
            return self.holdingQ.pop(0)
        else:
            return False

    def send_applySet_to_queue(self):
        """ Puts the message to apply set values to output onto the queue """
        self.holdingQ.append(
            ('applySet', (self.frames['SetU']['display'].value,
                          self.frames['SetI']['display'].value,
                          self.frames['SetCmd']['off_before_change'].get(),
                          self.frames['SetCmd']['on_after_change'].get())))
        self.set_set_by_app(False)

    def send_toggleRS_to_queue(self):
        """ Puts the message to toggleRS onto the queue """
        self.holdingQ.append((
            'toggleRS',
            '',
        ))
        self.update_runstop_display()

    def send_appQuit_to_queue(self):
        """ Puts the message to toggleRS onto the queue """
        #print("in send_appQuit_to_queue()")
        self.holdingQ.append((
            'appQuit',
            '',
        ))

    # Button Callbacks

    def update_and_write_config_file(self):
        """ Write config file"""
        for section in ('set', 'communication', 'memory_registers'):
            try:
                self.config[section]
            except (configparser.NoSectionError, KeyError):
                self.config[section] = dict()

        self.config.set('set', 'output_off_before_change',
                        f"{self.frames['SetCmd']['off_before_change'].get()}")
        self.config.set('set', 'output_on_after_change',
                        f"{self.frames['SetCmd']['on_after_change'].get()}")

        self.config.set('communication', 'comm',
                        self.frames['Config']['comm_text_box'].get())
        #self.config.set('communication','comm', self.frames['Config']['comm_text_box'])

        self.config.set(
            'memory_registers', 'memory_1_u',
            f"{self.frames['Mem']['registers'][1]['U']['display'].value:04}")
        self.config.set(
            'memory_registers', 'memory_1_i',
            f"{self.frames['Mem']['registers'][1]['I']['display'].value:04}")
        self.config.set(
            'memory_registers', 'memory_2_u',
            f"{self.frames['Mem']['registers'][2]['U']['display'].value:04}")
        self.config.set(
            'memory_registers', 'memory_2_i',
            f"{self.frames['Mem']['registers'][2]['I']['display'].value:04}")
        self.config.set(
            'memory_registers', 'memory_3_u',
            f"{self.frames['Mem']['registers'][3]['U']['display'].value:04}")
        self.config.set(
            'memory_registers', 'memory_3_i',
            f"{self.frames['Mem']['registers'][3]['I']['display'].value:04}")
        self.config.set(
            'memory_registers', 'memory_4_u',
            f"{self.frames['Mem']['registers'][4]['U']['display'].value:04}")
        self.config.set(
            'memory_registers', 'memory_4_i',
            f"{self.frames['Mem']['registers'][4]['I']['display'].value:04}")

        with open(self.config_path, 'w+') as configfile:
            self.config.write(configfile)

    def raise_command_method_frame(self):
        """raises either the 'serial' or 'network' frame to a visible state"""
        if self.frames['Config']['comm_method_text'].get() == 'Serial':
            self.frames['Config']['subframes']['serial'].tkraise()
        else:
            self.frames['Config']['subframes']['network'].tkraise()

    def inc_setu_by_one(self):
        """Increment the SetU display by 1"""
        self.frames['SetU']['display'] += 100
        self.set_set_by_app(True)

    def inc_setu_by_hundreth(self):
        """Increment the SetU display by 0.01"""
        self.frames['SetU']['display'] += 1
        self.set_set_by_app(True)

    def inc_setu_by_tenth(self):
        """Increment the SetU display by 0.1"""
        self.frames['SetU']['display'] += 10
        self.set_set_by_app(True)

    def dec_setu_by_one(self):
        """Decrement the SetU display by 1"""
        self.frames['SetU']['display'] -= 100
        self.set_set_by_app(True)

    def dec_setu_by_hundreth(self):
        """Decrement the SetU display by 0.01"""
        self.frames['SetU']['display'] -= 1
        self.set_set_by_app(True)

    def dec_setu_by_tenth(self):
        """Decrement the SetU display by 0.1"""
        self.frames['SetU']['display'] -= 10
        self.set_set_by_app(True)

    def inc_seti_by_one(self):
        """Increment the SetI display by 1"""
        self.frames['SetI']['display'] += 100
        self.set_set_by_app(True)

    def inc_seti_by_hundreth(self):
        """Increment the SetI display by 0.01"""
        self.frames['SetI']['display'] += 1
        self.set_set_by_app(True)

    def inc_seti_by_tenth(self):
        """Increment the SetI display by 0.1"""
        self.frames['SetI']['display'] += 10
        self.set_set_by_app(True)

    def dec_seti_by_one(self):
        """Decrement the SetI display by 1"""
        self.frames['SetI']['display'] -= 100
        self.set_set_by_app(True)

    def dec_seti_by_hundreth(self):
        """Decrement the SetI display by 0.01"""
        self.frames['SetI']['display'] -= 1
        self.set_set_by_app(True)

    def dec_seti_by_tenth(self):
        """Decrement the SetI display by 0.1"""
        self.frames['SetI']['display'] -= 10
        self.set_set_by_app(True)

    def memRecall1(self):
        """Button callback.  Recall Memory 1"""
        self.memRecall(1)

    def memRecall2(self):
        """Button callback.  Recall Memory 2"""
        self.memRecall(2)

    def memRecall3(self):
        """Button callback.  Recall Memory 3"""
        self.memRecall(3)

    def memRecall4(self):
        """Button callback.  Recall Memory 4"""
        self.memRecall(4)

    def memRecall0(self):
        """Button callback.  Recall values from PS and make set_by_app = False"""
        self.memRecall(0)

    def memRecall(self, mem_id):
        #print(f"in memRecall(), mem_id: {mem_id}")

        self.frames['SetU']['display'].value = self.frames['Mem']['registers'][
            mem_id]['U']['display'].value
        self.frames['SetI']['display'].value = self.frames['Mem']['registers'][
            mem_id]['I']['display'].value

        if mem_id == 0:
            self.set_set_by_app(False)

    def memStore1(self):
        """Button callback.  Store Memory 1"""
        self.memStore(1)

    def memStore2(self):
        """Button callback.  Store Memory 2"""
        self.memStore(2)

    def memStore3(self):
        """Button callback.  Store Memory 3"""
        self.memStore(3)

    def memStore4(self):
        """Button callback.  Store Memory 4"""
        self.memStore(4)

    def memStore(self, mem_id):
        #print(f"in memRecall(), mem_id: {mem_id}")

        self.frames['Mem']['registers'][mem_id]['U'][
            'display'].value = self.frames['SetU']['display'].value
        self.frames['Mem']['registers'][mem_id]['I'][
            'display'].value = self.frames['SetI']['display'].value


#  End of App() Class


#  Cooperative Processes
async def poll_ps_status(q: asyncio.Queue, ps: PS3010EC_Modbus):
    """asyncio process to poll PS periodically"""
    while True:
        #        print("in poll_ps_status()")
        await q.put(('polled_values', (ps.read_status_raw())))
        await asyncio.sleep(0.5)


async def get_next_event(q: asyncio.Queue, gui: App,
                         ps: PS3010EC_Modbus) -> None:
    """asyncio process to get events out of queue"""
    try:
        while True:
            #            print("in get_next_event()")
            event_type, parameters = await q.get()
            #print(f"event_type: {event_type}")
            #print(f"result: {result}")
            if event_type == 'polled_values':
                gui.update_last_polled_value(parameters)
            if event_type == 'toggleRS':
                ps.toggleRS()
            if event_type == 'applySet':
                ps.applySet(parameters)
            if event_type == 'appQuit':
                sys.exit(0)

    except Exception as e:
        print(repr(e))
        print(e)
        print("exit(1) from get_next_event()")
        sys.exit(1)


async def transfer_to_asyncQ(q: asyncio.Queue, gui: App) -> None:
    """asyncio process that pulls App events and places them on the asyncio Q

    Used to get modbus commands to the PS from the App

    """
    while True:
        event = gui.pop_next_holdingQ()
        if event:
            await q.put(event)
        await asyncio.sleep(.25)


async def service_gui_event_loop(gui: App) -> None:
    while True:
        #        print("in service_gui_event_loop()")
        gui.update()
        await asyncio.sleep(.25)


async def main():
    # Major components of the application
    q = asyncio.Queue()
    gui = App("Power Supply Control Interface", "800x600", q)
    #print(f"gui.frames['Config']['comm_text_box']: {gui.frames['Config']['comm_text_box'].get()}")
    try:
        ps = PS3010EC_Modbus(gui.frames['Config']['comm_text_box'].get(),
                             debug=False)
    except IOError as e:
        print(repr(e))
        print(e)
        sys.exit(1)

    # Cooperative processes
    poller = asyncio.create_task(poll_ps_status(q, ps))
    transfer = asyncio.create_task(get_next_event(q, gui, ps))
    put_on_Q = asyncio.create_task(transfer_to_asyncQ(q, gui))
    tk_looper = asyncio.create_task(service_gui_event_loop(gui))

    await asyncio.gather(poller,
                         transfer,
                         put_on_Q,
                         tk_looper,
                         return_exceptions=True)
    #await q.join()


if __name__ == "__main__":
    asyncio.run(main())
