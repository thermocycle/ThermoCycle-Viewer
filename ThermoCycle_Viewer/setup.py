

# ======================================================== #
# File automagically generated by GUI2Exe version 0.5.3
# Copyright: (c) 2007-2012 Andrea Gavana
# ======================================================== #

# Let's start with some default (for me) imports...

from cx_Freeze import setup, Executable
import sys, os, shutil

if len(sys.argv)==1:
    sys.argv+=['build','--build-exe=ThermoCycleViewer']

# Process the includes, excludes and packages first

include_files = []
includes = ['numpy','scipy.sparse.csgraph._validation']
excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'PyQt4',
            'pywin.debugger', 'pywin.debugger.dbgcon', 'pywin.dialogs',
            'tcl', 'Tkconstants', 'Tkinter','sympy','IPython']
packages = ['scipy','numpy']
path = []

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

import glob,os

include_files += ['logo_thermocycle.png',
                  'logo_thermocycle.ico',
                  'SQThesisModel.mat']
                  
import os, glob2, numpy, scipy
explore_dirs = [os.path.dirname(numpy.__file__), os.path.dirname(scipy.__file__)]

files = []
for d in explore_dirs:
    files.extend( glob2.glob( os.path.join(d, '**', '*.pyd') ) )

# Now we have a list of .pyd files; iterate to build a list of tuples into 
# include files containing the source path and the basename
for f in files:
    package_folder_path = os.path.normpath(os.path.join(os.path.dirname(numpy.__file__), '..')) + os.sep
    fn = f.split(package_folder_path, 1)[1].replace('\\', '.').split('.pyd', 1)[0]
    includes.append(fn)                  

# The setup for cx_Freeze is different from py2exe. Here I am going to
# use the Python class Executable from cx_Freeze

base = None
if sys.platform == "win32":
    base = "Win32GUI"

GUI2Exe_Target_1 = Executable(
    # what to build
    script = "GUI.py",
    initScript = None,
    base = base,
    targetDir = r"ThermoCycleViewer",
    targetName = "ThermoCycleViewer.exe",
    compress = True,
    copyDependentFiles = False,
    appendScriptToExe = False,
    appendScriptToLibrary = False,
    icon = 'logo_thermocycle.ico'
    )


# That's serious now: we have all (or almost all) the options cx_Freeze
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

import GUI
version = GUI.version

setup(
    
    version = version,
    description = "No Description",
    author = "No Author",
    name = "cx_Freeze Sample File",
    
    options = {"build_exe": {"include_files": include_files,
                             "includes": includes,
                             "excludes": excludes,
                             "packages": packages,
                             "path": path
                             }
               },
                           
    executables = [GUI2Exe_Target_1]
    )

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.
# 
if sys.platform.startswith('win'):
    import h5py
    h5py_path = os.path.dirname(h5py.__file__)
    shutil.copy2(h5py_path+'\\zlib1.dll','ThermoCycleViewer\\zlib1.dll')
    #Further windows packaging things
    import subprocess
    #Compress the files if UPX is found on the system path
    subprocess.call(['upx','ThermoCycleViewer/*.*'])
    #Make an installer using InnoSetup
    subprocess.call(['C:\Program Files (x86)\Inno Setup 5\Compil32.exe','/cc','innosetup.iss'])