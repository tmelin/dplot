#!/usr/bin/python
# Simple GUI implementation for gnuplot interface script
# Copyright Tomas Melin 2013-2014
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: iso-8859-1 -*-

from Tkinter import *
import tkFileDialog
import tkMessageBox
import plot
import shutil, os

import atexit

class plotapp(Frame):
    def __init__(self,parent,fn):
        Frame.__init__(self,parent)
        self.parent = parent #parent is argument given when creating
        self.initialize(fn)

    def initialize(self,fn):

        self.cb = [] #checkbuttons
        self.selected=[] #button on/off status
        self.cb_scaling=[] #scaling of signals
        self.b = Button()
        self.Lb = Listbox()
        self.scrollbar = Scrollbar()
        self.listmode = False #button style or list mode view

        self.setupMenu()
        
        self.txt = Text(self,borderwidth=1, height=6)#, state=DISABLED)
        self.txt.pack(fill="x", side="top", expand=0)
        self.frame = Frame(self, relief=RAISED, borderwidth=1)
        self.frame.pack(fill=BOTH, expand=1)
        self.pack(fill=BOTH, expand=1)
        plot.msgOut("Open file to begin plotting.",self)
        self.idir = 'C:' #default folder for opening file
        if fn != '' : #open directly if file name given on cmdline
            self.onOpen(fn)

    '''
        Create the menus
    '''
    def setupMenu(self) :

        menubar = Menu(self.parent, tearoff=0) #creates menu using main widget as base
        self.parent.config(menu=menubar) #created menubar is our menu
        
        fileMenu = Menu(menubar, tearoff=0) #tearoff to keep it from being tearable from menu
        fileMenu.add_command(label="Open", command=self.onOpen)
        menubar.add_cascade(label="File", menu=fileMenu)
        fileMenu.add_command(label="Exit", command=self.onExit)

        optionMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu = optionMenu)

        helpMenu = Menu(menubar,tearoff=0)
        menubar.add_cascade(label="Help", menu = helpMenu)
        about = Menu(helpMenu, tearoff = 0)
        helpMenu.add_command(label="About dplot", command=self.aboutInfo)


        self.lines = IntVar()
        self.linespoints = IntVar()
        
        lineOptions = Menu(optionMenu, tearoff =0) #menu for list styles
#        lineOptions.add_checkbutton(label="lines", variable = self.lines)
        lineOptions.add_checkbutton(label="linespoints", variable = self.linespoints)
        optionMenu.add_cascade(label="line styles", menu = lineOptions) #add to option menu
   
    '''
        Print about program info. Read info from file ABOUT
    '''
    def aboutInfo(self) :

        try :
            aboutText = open("./ABOUT","r")
            contents = aboutText.read()
            plot.msgOut(contents,self)
        except :
            plot.msgOut("Error opening ABOUT file",self)


    def getLineStyle(self) : #works but needs some development to get "exclusive" list
        if self.linespoints.get() :
            return "linespoints"
        else :
            return "lines"


    '''
        Actions when open file selected
    '''
    def onOpen(self, fl=''):
      
        ftypes = [('Supported types', '*.txt *.CSV *.log'),('All files', '*')] #win/unix works inverted

        if fl == '' :
            dlg = tkFileDialog.Open(self, filetypes = ftypes, initialdir = self.idir)
            fl = dlg.show()
        
        if fl != '':

            self.b.pack_forget() #forget plot button if one exists
            #forget drawn stuff if a new file is opened
            self.Lb.pack_forget()
            self.scrollbar.pack_forget()
            #remove buttons from frame in case a file already open. clear lists.
            for button in self.cb :
                button.pack_forget()
            for entry in self.cb_scaling :
                entry.pack_forget()

            self.idir = fl #save open file location for next time
            self.var_list = plot.get_varlist(fl,self)
            #create ch. buttons if small amount signals, otherwise, make dropdown sel. list (listmode)
            if len(self.var_list) < 9 :
                self.listmode = False
                self.createButtons()
            else :
                self.listmode = True
                self.createComboBox()
            self.var_arg = range(len(self.var_list))
            self.fn = (fl.split("/"))[-1] #get filename

            self.b = Button(self, text="Plot", command = self.onPlot)
            self.b.pack()
    '''
      Create a drop-down list type for showing signals
    '''
    def createComboBox(self) :

        self.scrollbar = Scrollbar(self.frame) 
        self.Lb = Listbox(self.frame,  yscrollcommand = self.scrollbar.set, selectmode=MULTIPLE, width=40) #several items sel.

        i=0 #enumerate vars
        for line in self.var_list :
            self.Lb.insert(END, str(i) +": "+ line)
            i=i+1

        self.selected=[] #signal on/off status
        self.scaling=[] #scaling, tbd for list

        #grow selection and checkbutton list as needed
        #ugly loop, but works
        for idx, var in enumerate(self.var_list) :
            self.selected.append(IntVar())
            self.scaling.append(StringVar())        

        self.scrollbar.pack( side = RIGHT, fill=Y )
        self.scrollbar.config( command = self.Lb.yview ) #connect scrollbar scrolling to listbox
        self.Lb.pack(side = RIGHT, fill=Y)

            
    '''
        Creates the checkbuttons according to file being opened
    '''
    def createButtons(self):

        self.cb = []
        self.cb_scaling=[]
        self.selected=[] #button on/off status
        self.scaling=[]
        #grow selection and checkbutton list as needed
        for idx, var in enumerate(self.var_list) :
            self.selected.append(IntVar())
            self.scaling.append(StringVar())
            self.cb.append(Checkbutton(self.frame, text = var, variable = self.selected[idx],\
                                          onvalue = 1, offvalue = 0, height=1))
            self.cb_scaling.append(Entry(self.frame, width=10,textvariable=self.scaling[idx]))
            self.cb[idx].pack(side=TOP,anchor=W)
            self.cb_scaling[idx].pack(side=TOP,anchor=W)
            self.cb_scaling[idx].insert(0, "1.0") #todo, scaling also for psl2 dl signals

    '''
        Actions when requesting plot
    '''
    def onPlot(self) :

        # in listmode, we need to do work to set selection
        # button mode selection is handled directly by gui
        if self.listmode :
            tup_sel = self.Lb.curselection()
#            print tup_sel
            self.selected = [IntVar(value=0)]*len(self.var_list)
            self.scaling = [StringVar(value=0)]*len(self.var_list)

            #activate selection and scale in plot list
            for idx in tup_sel :
                self.selected[int(idx)] = IntVar(value=1)
                self.scaling[int(idx)] = StringVar(value="1.0")       

        var_arg = []
        var_scale = []
        for idx,var in enumerate(self.selected) :
            if self.selected[idx].get() :
                var_arg.append(idx)
                var_scale.append(self.scaling[idx].get())
        if len(var_arg) < 1 :
            plot.msgOut("No signal(s) selected. Plotting all variables found.",self) 
            var_arg = range(len(self.var_list))
            for idx,var in enumerate(self.var_list) : #get all given scalings
                var_scale.append(self.scaling[idx].get())
                 
        plot.threaded_plot(self.var_list,self.fn,var_arg, var_scale, self)
    '''
        Exit program
    '''
    def onExit(self) :
        sys.exit(0)
        

        
def gui_main() :
    atexit.register(plot.cleanUp)
    root = Tk() #create top level Tk widget
    ww = 720 #px
    wh = 500 #px
    w = root.winfo_screenwidth() #screen
    h = root.winfo_screenheight()
    geo = str(ww)+"x"+str(wh)+"+"+str(w/2-ww/2)+"+"+str(h/2-wh/2)
    root.geometry(geo) #enough to fit 8 signals
    root.resizable(width=FALSE, height=TRUE) #disable resizing the window
    path = ''
    try:
        path = sys.argv[1]
    except:
        plot.msgOut("No input file given.")

    app = plotapp(root,path) #create file dialog
    root.title('DPlot file plotter')
#    img = PhotoImage(file='plot_icon.gif')
#    root.tk.call('wm', 'iconphoto', root._w, img)
    
    root.mainloop()


if __name__ == "__main__":
    gui_main()  
