#!/usr/bin/python
#script for interacting with gnuplot
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

import os, sys
import re
import shutil
import subprocess
import plot_gui
import time
from threading  import Thread

import plot
plot_recipe = "plot_recipe.mac" #name of recipe. Change as needed.


'''
    process given filename for plotting
'''
def preprocess(path,fn,obj=None):

    var_list=[]

    sourceFile = open(path, "r") #where to read from
    contents = sourceFile.readlines() #read in lines from file
    parsedFile = open("./plot/"+fn,"w") #open file for processed version

    if re.match('^VRLOG',contents[0]) :
        plot.msgOut("Found villaremote type trend file", obj)
        if not os.path.exists("./plot/plotsettings_"+fn) :
            plotSettings = open("./plot/plotsettings_"+fn, "w")
            plotSettings.write("set xdata time\n")
            plotSettings.write("set timefmt \"%Y-%m-%d-%H:%M:%S\"\n")
            plotSettings.close()
        vr_parse(contents, parsedFile, var_list)

    else :
        plot.msgOut("Could not recognize file format. Currently supported types are:\n-VR log files",obj)

    sourceFile.close()
    parsedFile.close()

    return var_list
'''
   parse villa remote log files
'''
def vr_parse(contents, parsedFile, var_list) :

    for line in contents :
        if re.match('^Date',line) :
            line = line.rstrip()
            l = line.split("\t")
            l = l[2:] #leave out time and date from varlist
            for i in l :
                var_list.append(i)

        elif not re.match('^\n',line) : #sort out empty lines
            line = line.split("\t")
            if len(line) > 2 :
                date = str(line[0]+"-"+line[1])
                line = line[2:]
                parsedFile.write(date)
                for item in line :
                    parsedFile.write("\t"+str(item))

    

'''
    Get list of variables from given path
'''
def get_varlist(path, obj=None) :

    try:
        os.stat("plot")
    except:
        os.mkdir("plot")
 
    fn = (path.split("/"))[-1] #get filename
    try:
        var_list = preprocess(path, fn, obj) 
        if len(var_list) < 1 :
            plot.msgOut("Warning: No signals found in selected file.", obj)
        else :
            plot.msgOut("Stripped nonnumerical values from %s, written to ./plot/" %fn, obj)
    except Exception as e:
        plot.msgOut(str(e),obj)
        plot.msgOut("Error in file or file not found.", obj)
        plot.msgOut(path, obj)
        return -1

    return var_list

'''
Do threaded plot. Normally only when used with GUI.

'''
def threaded_plot(var_list, fn, var_arg, var_scale, obj=None) :

    #create a new thread for every drawn plot
    t = Thread(target=draw_plot, args=(var_list, fn, var_arg, var_scale, obj))
    t.daemon = True # thread dies with the program if True
    t.start()
        
'''
 draw gnuplot according to request. Used as standalone or in thread.
 var_list = list of names of variables found
 fn = file name to plot from
 var_arg = list of vars to plot given as argument from user, e.g. [0,1,2]
''' 
def draw_plot(var_list, fn, var_arg, var_scale, obj=None) :

    try:
        gpl = subprocess.Popen("gnuplot",bufsize=1,stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    except OSError :
        msgOut("Error starting gnuplot, do you have it installed?\n\
        Also, check that it is in your PATH.",obj)
        return -1 #cannot go on

    #specific plotsettings for file type
    if os.path.exists("./plot/plotsettings_"+fn) :
        plotSet = open("./plot/plotsettings_"+fn, "r")
        setting = plotSet.readlines()
        for l in setting :
            gpl.stdin.write(l)
        plotSet.close()
        
    if os.path.exists(plot_recipe) :
        plot.msgOut("Found recipe "+ str(plot_recipe) +" for setting up plot.", obj)
        f_recipe = open(plot_recipe, "r")
        recipe = f_recipe.readlines()
        for ingredient in recipe : 
            gpl.stdin.write(ingredient)
        f_recipe.close()
    else :
        plot.msgOut("No plot recipe found, doing clean plot.", obj)
    
    if "darwin" in sys.platform : #use qt on os x for correct persist behaviour
        title = "set terminal qt title \""+fn+"\" \n"
    else :
        title = "set terminal wxt persist title \""+fn+"\" \n"
        
    gpl.stdin.write(title)

    if obj is not None :
        style = obj.getLineStyle()
    else :
        style = "lines"

    plot.msgOut("plotting selection: " + str(var_arg), obj)
    #generate a plot cmd that gnuplot understands
    plot_cmd = "plot "
    for idx, var in enumerate(var_arg) :
        plot_cmd += "\'./plot/"+fn+"\'"+" using 1:($"+str(int(var)+2)+"*"+str(var_scale[idx])+") title \'"+\
        var_list[int(var)]+"\' with "+style+", "
    plot_cmd = plot_cmd[:-2] ##ix version gnuplot needs this, removing last ","
    plot_cmd +=" \n" #Note: add a newline like this to actually generate plot
    if "win" in sys.platform :
        plot_cmd +=" pause mouse close \n" #IMPORTANT line for Windows. On Linux, leave out
    #pipe to gnuplot
    gpl.stdin.write(plot_cmd)
    gpl.stdin.flush()
    gpl.stdin.close()

    while True:
        line = gpl.stderr.readline() #thread blocks on stderr
        if not line:
            break
        plot.msgOut(line, obj, False)
    retcode = gpl.wait() #wait on child
    msgOut("Plot window closed. " + str(retcode), obj)

'''
    Prints out text to the text box (and possibly other places)
'''
def msgOut(text,obj=None, newline=True) :
    timeStr = time.strftime("%H:%M:%S") # obtains current time. On linux %T would do the trick
    if obj is not None and text.strip() != "gnuplot>" : #remove some bogus gnuplot> statements that arrives
        if newline :
            obj.txt.insert("1.0", timeStr+" "+text+"\n") #for messages during plotting. 1.0 is for first row, column 0 
            print text
        else :
            obj.txt.insert("1.0", timeStr+" "+text) #for messages during plotting. 1.0 is for first row, column 0
            print text.rstrip()
    else :
        print text

'''
    prints found variables
'''
def print_vars(var_list) :

    plot.msgOut( "found " +str(len(var_list)) + " variables")
    for idx, v in enumerate(var_list) :
        s = str(idx)+": "+str(v)
        plot.msgOut(s)
 
'''
    Main routine for terminal usage
'''
def cmd_main_plot() :

    var_arg =[]
    try:
        path = sys.argv[1]
    except:
        plot.msgOut("No input file given.")
        printHelp()
        return -1

    get_varlist(path)
 
    fn = (path.split("/"))[-1] #get filename
    try:
        var_list = preprocess(path, fn) 
        plot.msgOut("Stripped nonnumerical values from %s, written to ./plot/" %fn)
    except:
        plot.msgOut("Error in file or file not found.")
        plot.msgOut(path)
        return -1

    try : #process input arguments for how to plot
        '''
        input args accepted in form x-y or x,y,z ...
        '''
        args = sys.argv[2].split("-") # x-y type argument
        args2 = sys.argv[2].split(",") # a,b,c .. type argument
        if len(args) > 1 :
            var_arg = range(int(args[0]),int(args[1])+1) #+1 to get upper bound correctly
        elif len(args2) > 1 : #add all given arguments
            for a in range(len(args2)) :
                var_arg.append(int(args2[a]))
        else : #only one argument to plot
            var_arg = args[0]
    except :
        plot.msgOut("No vars selected or input error. Plotting all variables found.") 
        var_arg = range(len(var_list))

    var_scale = [1.0]*len(var_list) #default scale list needed

    try :
        draw_plot(var_list,fn,var_arg,var_scale)
        plot.msgOut("Showing requested plot.")
    except :
        plot.msgOut("Error in using gnuplot or bad plot selection.")
        printHelp()
        return -1

    cleanUp()


def cleanUp() :

    try :
        if os.path.exists("./plot") :
            plot.msgOut("removing temp ./plot directory before quitting.")
            shutil.rmtree("./plot");
    except :
        plot.msgOut("Failed removing ./plot")

def printHelp() :
    plot.msgOut("Usage: plot.py [selection] filename\n selection takes form x-y or x,y,z...") 

if __name__ == "__main__":
    cmd_main_plot()
