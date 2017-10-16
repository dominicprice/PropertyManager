#MIT License
#
#Copyright (c) 2017 Dominic Price
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

#Import GUI modules
import tkinter as tk
import tkinter.ttk
import tkinter.font
import tkinter.filedialog
import tkinter.messagebox
import tkinter.simpledialog

import os.path #For filesystem functions
import argparse #Process command line arguments
import xml.etree.ElementTree as ET #Read/write XML


class Globals:
	"""Contains global project variables and functions as static members."""
	proj_title = "Visual Studio Property Manager"
	proj_author = "Dominic Price"
	proj_version = "1.0"
	xmlns = "http://schemas.microsoft.com/developer/msbuild/2003"

	def basename(path):
		"""Converts a filepath into the filename with no extension."""
		return os.path.basename(path).rsplit('.', 1)[0]

class Project():
	"""
	Stores the xml tree of a Visual Studio project file (.vcxproj) and provides
	methods to get/set elements.
	"""
	def __init__(self, filename):
		"""Construct a Project object from the path to a Visual Studio project file."""
		self.filename = filename
		self.tree = ET.parse(filename)
		self.root = self.tree.getroot()

	def get_configs(self):
		"""Get the configurations associated with the project."""
		return [cc.get('Include') 
			for c in self.root.findall("{{{}}}ItemGroup".format(Globals.xmlns))
			if c.get('Label') == "ProjectConfigurations"
			for cc in c 
			if 'Include' in cc.attrib
		]

	def get_props(self, configuration):
		"""Get the list of custom property sheets the project loads when 'configuration' is active."""
		return [Globals.basename(cc.get('Project'))
			for c in self.root.findall("{{{}}}ImportGroup".format(Globals.xmlns))
			if c.get('Label') == "PropertySheets" and configuration in c.get('Condition')
			for cc in c
			if 'Condition' not in cc.attrib
		]

	def add_prop(self, configuration, prop_path):
		"""Add a property sheet for a configuration in the project."""
		for c in self.root.findall("{{{}}}ImportGroup".format(Globals.xmlns)):
			if c.get('Label') == "PropertySheets" and configuration in c.get('Condition'):
				new_prop = ET.Element("Import", {"Project": prop_path})
				c.append(new_prop)
		self.tree.write(self.filename)

	def remove_prop(self, configuration, prop_name):
		"""Remove a property sheet for a configuration in the project."""
		for c in self.root.findall("{{{}}}ImportGroup".format(Globals.xmlns)):
			if c.get('Label') == "PropertySheets" and configuration in c.get('Condition'):
				for cc in c:
					if 'Condition' not in cc.attrib and prop_name in cc.get('Project'):
						c.remove(cc)
		self.tree.write(self.filename)


class PropSheet(tk.Toplevel):
	"""
	Stores the xml tree of a property sheet (.props) and creates a window to allow
	modification of the property sheet fields.
	"""
	def __init__(self, master, filename):
		"""Construct a PropSheet window from a root window and the path to a Property Sheet."""
		super().__init__(master)
		#Create xml tree
		self.filename = filename
		self.tree = ET.parse(filename)
		self.root = self.tree.getroot()
		self.item_def_group = self.root.find("{{{}}}ItemDefinitionGroup".format(Globals.xmlns))

		#Populate the window with widgets
		self.populate_widgets()
		self.title("Property Sheet Editor")

		#Load xml data into widgets
		self.update_items()

	def include_node(self):
		"""Returns the xml element containing include paths."""
		return self.item_def_group.find("{{{}}}ClCompile".format(Globals.xmlns))\
			.find("{{{}}}AdditionalIncludeDirectories".format(Globals.xmlns))

	def libdir_node(self):
		"""Returns the xml element containing library directories."""
		return self.item_def_group.find("{{{}}}Link".format(Globals.xmlns))\
			.find("{{{}}}AdditionalLibraryDirectories".format(Globals.xmlns))

	def libdep_node(self):
		"""Returns the xml element containing library dependencies."""
		return self.item_def_group.find("{{{}}}Link".format(Globals.xmlns))\
			.find("{{{}}}AdditionalDependencies".format(Globals.xmlns))

	def preproc_node(self):
		"""Returns the xml element containing preprocessor definitions."""
		return self.item_def_group.find("{{{}}}ClCompile".format(Globals.xmlns))\
			.find("{{{}}}PreprocessorDefinitions".format(Globals.xmlns))

	def insert(self, element, text):
		"""Adds a string to an element with semi-colon deliminated text."""
		if element.text == None or element.text.strip() == "":
			element.text = text
		else:
			element.text = text + ';' + element.text.strip()

	def remove(self, element, text):
		"""Removes a string from an element with semi-colon deliminated text."""
		if text + ';' in element.text:
			element.text = element.text.replace(text + ';', '')
		else:
			element.text = element.text.replace(text, '')

	def parse_text(self, element):
		"""Returns a list of strings from an element with semi-colon deliminated text."""
		if element.text == None or element.text.strip() == "":
			return []
		return [item.strip() for item in element.text.split(';')]
		

	def add_inc(self):
		"""Prompts for an include path and adds to the property sheet."""
		inc_dir = tk.filedialog.askdirectory(title="Select include directory")
		if inc_dir == None:
			return
		
		self.insert(self.include_node(), inc_dir)
		self.tree.write(self.filename)
		self.update_items()

	def remove_inc(self, inc_dir):
		"""Removes an include path from the property sheet."""
		self.remove(self.include_node(), inc_dir)
		self.tree.write(self.filename)
		self.update_items()

	def add_libdir(self):	
		"""Prompts for a library directory and adds to the property sheet."""
		lib_dir = tk.filedialog.askdirectory(title="Select library directory")
		if lib_dir == None:
			return

		self.insert(self.libdir_node(), lib_dir)
		self.tree.write(self.filename)
		self.update_items()

	def remove_libdir(self, lib_dir):
		"""Removes a library directory from the property sheet."""
		self.remove(self.libdir_node(), lib_dir)
		self.tree.write(self.filename)
		self.update_items()

	def add_libdep(self):
		"""Prompts for a library dependency and adds to the property sheet."""
		deps = [Globals.basename(dep) for dep in
					tk.filedialog.askopenfilenames(
						title="Select library files", 
						filetypes=(("Library file", "*.lib"), ("All Files", "*.*")))]

		for dep in deps:
			self.insert(self.libdep_node(), dep)
		self.tree.write(self.filename)
		self.update_items()

	def remove_libdep(self, dep):
		"""Removes a library dependency from the property sheet."""
		self.remove(libdep_node(), dep)
		self.tree.write(self.filename)
		self.update_items()

	def add_preproc(self):
		"""Promps for a preprocessor definition and adds to the property sheet."""
		defn = tk.simpledialog.askstring("Add Preprocessor Definition", "Please enter the preprocessor definition")
		if defn == None:
			return

		self.insert(preproc_node(), defn)
		self.tree.write(self.filename)
		self.update_items()
	
	def remove_preproc(self, defn):
		"""Removes a preprocessor definition from the property sheet."""
		self.remove(self.preproc_node(), defn)
		self.tree.write(self.filename)
		self.update_items()

	def update_items(self):
		"""Populates listbox widgets with contents of the property sheet."""
		self.w_include_list.delete(0, tk.END)
		for item in self.parse_text(self.include_node()):
			self.w_include_list.insert(tk.END, item)

		self.w_libdir_list.delete(0, tk.END)
		for item in self.parse_text(self.libdir_node()):
			self.w_libdir_list.insert(tk.END, item)

		self.w_libdep_list.delete(0, tk.END)
		for item in self.parse_text(self.libdep_node()):
			self.w_libdep_list.insert(tk.END, item)

		self.w_preproc_list.delete(0, tk.END)
		for item in self.parse_text(self.preproc_node()):
			self.w_preproc_list.insert(tk.END, item)

	def populate_widgets(self):
		"""Constructor function, creates and displays all widgets."""
		listbox_width = 70

		#Create widgets
		self.w_title = tk.Label(self,
							text="Editing property sheet '{}'".format(Globals.basename(self.filename)),
							font=tk.font.Font(size=13))

		self.w_include_label = tk.Label(self,
							text="Include\nDirectories",
							justify=tk.RIGHT)
		self.w_include_list = tk.Listbox(self, 
							width=listbox_width)

		self.w_libdir_label = tk.Label(self,
							text="Library\nDirectories",
							justify=tk.RIGHT)
		self.w_libdir_list = tk.Listbox(self, 
							width=listbox_width)

		self.w_libdep_label = tk.Label(self,
							text="Dependencies",
							justify=tk.RIGHT)
		self.w_libdep_list = tk.Listbox(self, 
							width=listbox_width)

		self.w_preproc_label = tk.Label(self,
							text="Preprocessor\nDefinitions",
							justify=tk.RIGHT)
		self.w_preproc_list = tk.Listbox(self, 
							width=listbox_width)

		#Make context menus and bind them to right-clicks on the appropriate listbox
		inc_menu = tk.Menu(self, tearoff=0)
		inc_menu.add_command(label="Add...", command=lambda: self.add_inc())
		inc_menu.add_command(label="Remove", command=lambda: self.remove_inc(self.w_include_list.get(tk.ACTIVE)))
		self.w_include_list.bind("<Button-3>", lambda e: inc_menu.tk_popup(e.x_root, e.y_root, 0))

		libdir_menu = tk.Menu(self, tearoff=0)
		libdir_menu.add_command(label="Add...", command=lambda: self.add_libdir())
		libdir_menu.add_command(label="Remove", command=lambda: self.remove_libdir(self.w_libdir_list.get(tk.ACTIVE)))
		self.w_libdir_list.bind("<Button-3>", lambda e: libdir_menu.tk_popup(e.x_root, e.y_root, 0))

		libdep_menu = tk.Menu(self, tearoff=0)
		libdep_menu.add_command(label="Add...", command=lambda: self.add_libdep())
		libdep_menu.add_command(label="Remove", command=lambda: self.remove_libdep(self.w_libdep_list.get(tk.ACTIVE)))
		self.w_libdep_list.bind("<Button-3>", lambda e: libdep_menu.tk_popup(e.x_root, e.y_root, 0))

		preproc_menu = tk.Menu(self, tearoff=0)
		preproc_menu.add_command(label="Add...", command=lambda: self.add_preproc())
		preproc_menu.add_command(label="Remove", command=lambda: self.remove_preproc(self.w_preproc_list.get(tk.ACTIVE)))
		self.w_preproc_list.bind("<Button-3>", lambda e: preproc_menu.tk_popup(e.x_root, e.y_root, 0))

		#Place widgets
		self.w_title.grid(row=0, column=0, columnspan=2)
		self.w_include_label.grid(row=1, column=0, sticky=tk.N+tk.E)
		self.w_include_list.grid(row=1, column=1)
		self.w_libdir_label.grid(row=2, column=0, sticky=tk.N+tk.E)
		self.w_libdir_list.grid(row=2, column=1)
		self.w_libdep_label.grid(row=3, column=0, sticky=tk.N+tk.E)
		self.w_libdep_list.grid(row=3, column=1)
		self.w_preproc_label.grid(row=4, column=0, sticky=tk.N+tk.E)
		self.w_preproc_list.grid(row=4, column=1)


class PropertyManager(tk.Frame):
	"""
	Creates a Frame providing an interface to add or remove property sheets from
	a Visual Studio project.
	"""
	def __init__(self, master, default_filepath="", prop_dir=os.path.dirname(os.path.realpath(__file__))):
		"""Construct a PropertyManager object from a tk Window, and optionally a default path to a 
		   project file and a directory containing propery sheets."""
		super().__init__(master)

		#Create program variables
		self.configuration = tk.StringVar(self) #Current project configuration
		self.project_file = tk.StringVar(self) #Filepath of the project
		self.project = None #Project object containing the current project
		self.prop_dir = tk.StringVar(self) #Directory of the property files
		self.props = []

		#Set program variables
		self.project_file.set(default_filepath)
		self.prop_dir.set(prop_dir)
		
		#Populate with widgets and display everything
		self.pack(fill=tk.BOTH, expand=1)
		self.populate_widgets()

		#Ensure window isn't resized too small
		master.update()
		master.minsize(root.winfo_width(), root.winfo_height())
		master.title(Globals.proj_title)

		#Bind events
		self.w_proj_button.bind("<Button-1>", lambda e: self.select_project_file()) #Show file dialog for project
		self.w_prop_button.bind("<Button-1>", lambda e: self.select_property_dir()) #Show file dialog for prop_dir
		self.project_file.trace("w", lambda e, *args: self.load_project_file()) #Load the new project file
		self.configuration.trace("w", lambda e, *args: self.load_config_props()) #Load property sheets associated with a configuration
		self.w_activate_button.bind("<Button-1>", lambda e: self.activate()) #Add currently selected property file to the project
		self.w_deactivate_button.bind("<Button-1>", lambda e: self.deactivate()) #Remove the currently selected property file from the project
		self.w_add_button.bind("<Button-1>", lambda e: self.add_prop()) #Open the prompt to create a new property file
		self.w_edit_button.bind("<Button-1>", lambda e: self.edit_prop()) #Open the prompt to edit a property file
		self.w_copy_button.bind("<Button-1>", lambda e: self.copy_prop()) #Open the prompt to copy a property file
		self.w_remove_button.bind("<Button-1>", lambda e: self.remove_prop()) #Open the prompt to delete a promperty file

		#Get the ball rolling
		self.load_project_file()
		self.load_config_props()

	def populate_widgets(self):
		"""Constructor function, creates and displays all widgets."""
		#Create widgets
		self.w_title = tk.Label(self, 
						text=Globals.proj_title,
						font=tk.font.Font(size=14),
						padx=5)
		self.w_author = tk.Label(self,
						text="Version " + Globals.proj_version + " by " + Globals.proj_author,
						pady=2)

		self.w_prop_frame = tk.Frame(self,
						padx=5,
						pady=5)
		self.w_prop_label = tk.Label(self.w_prop_frame,
						text="Props Dir:")
		self.w_prop_input = tk.Entry(self.w_prop_frame,
						textvariable=self.prop_dir)
		self.w_prop_button = tk.Button(self.w_prop_frame,
						text="...")

		self.w_proj_frame = tk.Frame(self,
						padx=5,
						pady=5)
		self.w_proj_label = tk.Label(self.w_proj_frame,
						text="Project File: ")
		self.w_proj_input = tk.Entry(self.w_proj_frame,
						textvariable=self.project_file)
		self.w_proj_button = tk.Button(self.w_proj_frame,
						text="...")

		self.w_config_frame = tk.Frame(self)
		self.w_config_label = tk.Label(self.w_config_frame,
						text="Select Configuration")
		self.w_config_select = tk.OptionMenu(self.w_config_frame,
						self.configuration, "")

		self.w_active_libs = tk.Listbox(self)
		self.w_active_libs.insert(tk.END, "Property files currently in project:")
		self.w_active_libs.itemconfig(0, fg="grey")
		self.w_inactive_libs = tk.Listbox(self)
		self.w_inactive_libs.insert(tk.END, "Property files currently not in project:")
		self.w_inactive_libs.itemconfig(0, fg="grey")

		self.w_set_active_frame = tk.Frame(self,
						padx=20)
		self.w_activate_button = tk.Button(self.w_set_active_frame,
						text="^",
						width=2)
		self.w_deactivate_button = tk.Button(self.w_set_active_frame,
						text="v",
						width=2)

		self.w_buttons_frame = tk.Frame(self)
		self.w_add_button = tk.Button(self.w_buttons_frame,
						text="Add")
		self.w_edit_button = tk.Button(self.w_buttons_frame,
						text="Edit")
		self.w_copy_button = tk.Button(self.w_buttons_frame,
						text="Copy")
		self.w_remove_button = tk.Button(self.w_buttons_frame,
						text="Remove")

		self.status_bar_frame = tk.Frame(self,
						bd=1,
						relief=tk.SUNKEN)
		self.status_bar = tk.Label(self.status_bar_frame, 
						text="Ready",
						anchor=tk.W)

		#Place widgets
		self.w_title.pack()
		self.w_author.pack()

		tk.ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, expand=1)

		self.w_proj_frame.pack(fill=tk.X, expand=1)
		self.w_proj_label.pack(side=tk.LEFT)
		self.w_proj_input.pack(side=tk.LEFT, fill=tk.X, expand=1)
		self.w_proj_button.pack(side=tk.LEFT)

		self.w_prop_frame.pack(fill=tk.X, expand=1)
		self.w_prop_label.pack(side=tk.LEFT)
		self.w_prop_input.pack(side=tk.LEFT, fill=tk.X, expand=1)
		self.w_prop_button.pack(side=tk.LEFT)

		self.w_config_frame.pack(fill=tk.X, expand=1)
		self.w_config_label.pack(side=tk.LEFT)
		self.w_config_select.pack(side=tk.LEFT, fill=tk.X, expand=1)

		self.w_active_libs.pack(fill=tk.BOTH, expand=1)

		self.w_set_active_frame.pack(fill=tk.X, expand=1)
		self.w_activate_button.pack(side=tk.LEFT, fill=tk.X, expand=1)
		self.w_deactivate_button.pack(side=tk.LEFT, fill=tk.X, expand=1)

		self.w_inactive_libs.pack(fill=tk.BOTH, expand=1)

		self.w_buttons_frame.pack()
		self.w_add_button.pack(side=tk.LEFT)
		self.w_edit_button.pack(side=tk.LEFT)
		self.w_copy_button.pack(side=tk.LEFT)
		self.w_remove_button.pack(side=tk.LEFT)

		self.status_bar_frame.pack(fill=tk.X)
		self.status_bar.pack(fill=tk.X)

	def set_status_bar(self, s):
		"""Sets the current message displayed on the status bar."""
		self.status_bar.config(text=s)
		self.status_bar.update_idletasks()

	def select_project_file(self):
		"""Displays a file browser to prompt for a project file then sets the project filepath to this."""
		self.project_file.set(tk.filedialog.askopenfilename(
			filetypes=(("Visual Studio Project", "*.vcxproj"), ("All Files", "*.*"))
		))
		return "break"

	def select_property_dir(self):
		"""Displays a file browser to prompt for a property sheet directory then sets the prop directory to this."""
		self.prop_dir.set(tk.filedialog.askdirectory())
		self.load_config_props()
		return "break"

	def is_valid_project(self):
		"""Returns true if the current project filepath points to a valid project file."""
		if not os.path.isfile(self.project_file.get()):
			return False
		#Do other checks...
		return True

	def load_project_file(self):
		"""Loads a project file into memory and updates widgets to reflect this."""
		self.set_status_bar("Loading project file...")

		#Stop any action while path given is not a valid project
		if not self.is_valid_project():
			self.project = None
			self.w_proj_label.config(fg="red")
			self.configuration.set("")
			self.w_config_select['menu'].delete(0, 'end')
			self.set_status_bar("Project file is invalid")
			return
		
		#Load the project into memory
		self.w_proj_label.config(fg="green")
		self.project = Project(self.project_file.get())

		#Update list of project configurations
		self.w_config_select['menu'].delete(0, 'end')
		choices = self.project.get_configs()
		if (len(choices) > 0):
			self.configuration.set(choices[0])
		for choice in choices:
			self.w_config_select['menu'].add_command(label=choice, command=tk._setit(self.configuration, choice))

		self.set_status_bar("Ready")

	def load_config_props(self):
		"""Updates widgets to display which property sheets are active and inactive for the current configuration."""
		self.set_status_bar("Populating property sheets...")

		#Clear list
		self.w_active_libs.delete(1, tk.END)
		self.w_inactive_libs.delete(1, tk.END)

		#Find all property sheets
		self.props = [Globals.basename(file) for file in os.listdir(self.prop_dir.get()) if file.endswith(".props")]

		#Put all property sheets in 'inactive' if no project currently loaded
		if self.project == None:
			for prop in self.props:
				self.w_inactive_libs.insert(tk.END, prop)
			self.set_status_bar("Project file is invalid")
			return

		#Sort and display property sheets as active or inactive
		cur_props = self.project.get_props(self.configuration.get())
		for prop in self.props:
			if prop in cur_props:
				self.w_active_libs.insert(tk.END, prop)
			else:
				self.w_inactive_libs.insert(tk.END, prop)

		self.set_status_bar("Ready")

	def selected_prop(self, position=None):
		"""Returns a string containing the name of the currently selected property sheet. Can specify
		   whether to only allow an 'active' or 'inactive' property sheet with the position argument."""
		if any(x in str(self.w_inactive_libs.curselection()) for x in ["()", "0"]):
			if any(x in str(self.w_active_libs.curselection()) for x in ["()", "0"]):
				return None
			if position == "inactive":
				return None
			return self.w_active_libs.get(tk.ACTIVE)
		if position == "active":
			return None
		return self.w_inactive_libs.get(tk.ACTIVE)


	def activate(self):
		"""Adds the currently selected property sheet to the project."""
		if self.project == None or self.selected_prop("inactive") == None:
			return "break"
		self.project.add_prop(self.configuration.get(), os.path.join(self.prop_dir.get(), self.selected_prop("inactive") + ".props"))
		self.load_config_props()
		return "break"

	def deactivate(self):
		"""Removes the currently selected property sheet from the project."""
		if self.project == None or self.selected_prop("active") == None:
			return "break"
		self.project.remove_prop(self.configuration.get(), self.selected_prop("active"))
		self.load_config_props()
		return "break"

	def add_prop(self):
		"""Presents a prompt to create a new property sheet."""
		#Prompt for name of the new property sheet
		new_name = tk.simpledialog.askstring("New property sheet name", "Enter a name for the new library", initialvalue="mylib")
		if new_name == None:
			return "break"

		#Create a file for the property sheet and fill with the basic xml tree
		new_name = os.path.join(self.prop_dir.get(), new_name + ".props")
		with open(new_name, "w+") as f:
			f.write('<?xml version="1.0" encoding="utf-8"?><Project ToolsVersion="4.0" '
			'xmlns="http://schemas.microsoft.com/developer/msbuild/2003"><ImportGroup '
			'Label="PropertySheets" /><PropertyGroup Label="UserMacros" /><ItemDefinitionGroup>'
			'<ClCompile><AdditionalIncludeDirectories></AdditionalIncludeDirectories><Preprocesso'
			'rDefinitions></PreprocessorDefinitions></ClCompile><Link><AdditionalLibraryDirectori'
			'es></AdditionalLibraryDirectories><AdditionalDependencies></AdditionalDependencies>'
			'</Link></ItemDefinitionGroup><ItemGroup /></Project>')

		#Open the property sheet editor
		PropSheet(self, new_name)
		self.load_config_props()
		return "break"

	def edit_prop(self):
		"""Presents a prompt to edit the currently selected property sheet."""
		if self.selected_prop() == None:
			tk.messagebox.showerror("Error", "No property sheet selected")
			return "break"

		#Open the property sheet editor
		PropSheet(self, os.path.join(self.prop_dir.get(), self.selected_prop() + ".props"))
		return "break"

	def copy_prop(self):
		"""Presents a prompt to copy the currently selected property sheet."""
		if self.selected_prop() == None:
			tk.messagebox.showerror("Error", "No property sheet selected")
			return "break"

		old_name = self.selected_prop()

		#Prompt for name of the new property sheet
		new_name = tk.simpledialog.askstring("New property sheet name", "Enter a name for the new library", 
									   initialvalue=old_name + "_copy")
		new_name = os.path.join(self.prop_dir.get(), new_name + ".props")

		#Copy the data from the existing property sheet to a new file
		with open(os.path.join(self.prop_dir.get(), old_name + ".props")) as f:
			data = f.readlines()
		with open(new_name, "w+") as f:
			for line in data:
				f.write(line)

		self.load_config_props()
		return "break"

	def remove_prop(self):
		"""Deletes a property sheet file."""
		if self.selected_prop() == None:
			tk.messagebox.showerror("Error", "No property sheet selected")
			return "break"

		#Ask the user if they really want to delete the property sheet
		really_delete = tk.messagebox.askyesno("Really delete?",
			"Are you sure you want to delete the file {}?\n"
			"Warning: If other projects use this property file this may cause conflicts".format(self.selected_prop()))

		if really_delete:
			os.remove(os.path.join(self.prop_dir.get(), self.selected_prop() + ".props"))
			self.load_config_props()
		return "break"


#Process command line options
parser = argparse.ArgumentParser(
	description=Globals.proj_title + ". Add or remove property files containing include and library path information from a Visual Studio project",
	epilog="Created by " + Globals.proj_author + ", 2017. Contact at dominicprice@outlook.com for any issues or suggestions")
parser.add_argument('filepath', default="", nargs='?', type=str, help="Filepath to the project file")
parser.add_argument("-p, --prop-dir", default="", dest="prop_dir", nargs=1, help="Directory where the property files are located")
parser.add_argument('--version', action='version', version="%(prog)s " + Globals.proj_version)
args = parser.parse_args()

#Register the namespace
ET.register_namespace('', Globals.xmlns)

#Create window and run!
root = tk.Tk()
app = PropertyManager(
	master=root, 
	default_filepath=args.filepath,
	prop_dir=os.path.dirname(os.path.realpath(__file__)) if args.prop_dir == "" else args.prop_dir[0]
	)
app.mainloop()