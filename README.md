dplot
=====

Plotting tool for data files using gnuplot as plot engine

Dplot is a wrapper for gnuplot. It was written for easy plotting of
supported file types using gnuplot as the plotting engine.
Written in Python and tested on Linux, Win 7 and OS X.
Dplot can be used directly from the command line (plot.py) or using
a simple gui (plot_gui.py). It is a tool aimed at stream-lining plotting
of log files containing measurements saved using different logging tools.
It opens the file to plot, tries to automatically determine the file format,
and extracts the signal names. It plots the requested signals from the log file.

Release 1.0 only support one type of data files, however new file formats can be 
added into the preprocess() function. 

Make sure to have gnuplot(gnuplot.info) installed prior to using this program. 
