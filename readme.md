# PropertyManager

_Property manager_ is  GUI tool to facilitate creating, editing and adding property sheets to projects in Visual Studio. Its main purpose is to make adding libraries to a Visual Studio project simple and so provides a simple interface which makes it possible to easily add and remove **Include Paths**, **Library Directories**, **Dependencies** and **Preprocessor Definitions** to a property sheet.

## Features
* Simple to get running
* Only depends on Python and its standard library
* Easily integrates into Visual Studio
* Removes the manual labour involved in organising and populating property sheets

## Installation
If you have git installed then simply clone [this project](https://github.com/dominicprice/PropertyManager) into an easily accessible directory (e.g. _C:/cpp/PropertyManager_). If you don't have git installed then you'll need to download the files **PropertyManager.py** and **stdlib.props** into this directory. If you don't need access from within Visual Studio then you're ready to go! Simply double-click on **PropertyManager.pyw** if your computer associates .pyw files with Python already, otherwise launch a command prompt in the installation folder and type `pythonw PropertyManager.pyw` to launch. (NB: pythonw is the same as python but suppresses the console.)

### Making a Visual Studio External Tool
Integration with Visual Studio makes it easier to change the property sheets associated with you project and is (almost) as simple to set up. From within Visual Studio, go to the _Tools_ menu and click on _External Tools..._ and press the _Add_ button. 
* In the _Title_ field, type `Property Manager` (or whichever name most suits your fancy)
* In the command field type `pythonw.exe` (if python is not in your system's PATH then you'll need to provide the full path to the pythonw executable e.g. `C:/python36/pythonw.exe`)
* In the arguments field type `C:/cpp/PropertyManager/PropertyManager.pyw $(ProjectDir)/$(ProjectFileName)` (if you installed to a different directory then replace `C:/cpp/PropertyManager` with your installation directory)
* Press _OK_

You can now launch Property Manager by opening the _Tools_ menu and clicking _Property Manager_ (or whatever you called it). Make sure to save you project (by pressing `Ctrl`+`Shift`+`S`) before launching Property Manager otherwise Visual Studio will get annoyed that we've edited the project file while it still has changes it hasn't yet written to the project.

When you close the Property Manager, Visual Studio will display a prompt asking you how to deal with the project file having been modified, simply click _Reload_. If you forgot to save before loading the Property Manager it will display a different prompt, press _Overwrite_ if you didn't make any manual changes to the project's property sheets since you last saved as Property Manager only modifies this part of the project file so there will be no conflicts, if not it is best to press _Ignore_, save the project and rerun the Propety Manager.

_NB: The `$(ProjectDir)/$(ProjectFileName)` argument tells Propery Manager to automatically load in the current project file, however this can be omitted or modified if you prefer it to start with a different file._

## Usage
Property Manager's GUI is fairly self-explanatory, but here is a discussion about usage. The main thing to note is that actions take affect instantly; there is no save button to press.
### Main Window
The two text inputs at the top of the window are the paths to the project file and property sheet directory. The two listboxes underneath display the property sheets currently in the project (at the top) and not in the project (at the bottom). If the project file does not exist then it will appear in red and all property sheets will appear in the bottom listbox, however it is still possible to use the Add, Edit, Copy and Remove buttons in this state.

Only property sheets inside the active property sheet directory will be shown, any other property sheets linked in the project are ignored, so it is recommended that if you use Property Manager on an existing project you check to make sure there are no possibly conflicting property sheets already linked to it.

Clicking the Add button will prompt you for a name to give a new property sheet, it will be created in the directory you have chosen as the active property sheet directory. The Copy button will also prompt you for a name to give the copy of the property sheet and will create that copy in the active property sheet directory. The Remove button deletes the currently selected property sheet, however it will not unlink the property sheet from any projects that currently use that property sheet (other than the active project if there is one) so make sure that it is not in use before removing it. The Edit button opens up the property sheet editor discussed below.
### Property Sheet Editor
The property sheet editor is displayed after creating a new property sheet or on clicking the Edit button. It displays four listboxes containing the current values stored in the property sheet for Include Paths, Library Directories, Dependencies and Preprocessor Definitions. To add or remove items from these listboxes, right click on them and press the corresponding action. Clicking Add will open a prompt for you to add the name of the new item; for Include Paths and Library Directories this is a file browser that accepts folders, for Dependencies this is a file browser that accepts one or more files, and for Preprocessor Definitions this is a text entry box. Note that the Remove option does not prompt to ask if you are sure before removing the item from the property sheet.
### Command Line Arguments
Property Manager can be invoked using command line arguments, one optional positional argument containing the path of the project it should launch with as the active project (if unspecified no project will be loaded by default), and another optional argument prepended with '-p' or '--prop-dir' containing the directory it should launch with as the active property  sheet directory (if not specified the directory the script is placed in will be used as the default directory). For example, invoking `pythonw PropertyManager.py C:\cpp\source\MyProject\MyProject.vcxproj -p C:\cpp\customprops` will launch the Property Manager with the MyProject.vcxproj project loaded and _C:\cpp\customprops_ as the active property sheet directory.