"""
Copyright (C) 2022-2024  Amelia Sutton
This software is distributed under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version. See the file "[COPYING](COPYING)" for more details.
"""
from tkcalendar import DateEntry
import psycopg as postgres
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import sv_ttk
import sys
import os
from datetime import datetime
import re
import winsound
import csv
import dotenv
import logging
from adapters.script_files import ScriptFiles
import parameterized_scripts
from parameterized_scripts import ParameterType, ParameterDefinition, ParameterValue, ParameterValidationError

# Object for executing queries
class Querier:
    def __init__(self):
        self.query_name = ''
        logging.info("Querier Initialized Successfully.")

    def connect(self):
        logging.info("Connecting to LDlite database...")
        try:
            self.connection = postgres.connect(f'dbname={os.getenv("dbname")} user={os.getenv("user")} password={os.getenv("password")} host={os.getenv("host")} port={os.getenv("port")}')
            self.cursor = postgres.ClientCursor(self.connection)
        except Exception as e:
            PopupWindow(e)
            raise e
        logging.info("LDlite database connection established!")

    def disconnect(self):
        logging.info("Closing database connection...")
        self.cursor.close()
        
    def rollbackTransaction(self):
        try:
            self.cursor.execute('ROLLBACK')
        except Exception as e:
            raise e

    def parseParameters(self, script:str) -> list[str]:
        logging.info(f"Parsing parameters...")
        paramlist = re.findall('\{.*?\}', script)
        for i, item in enumerate(paramlist):
            item = item [1:-1]
            paramlist[i] = item
        return paramlist

    def runQuery(self, script:str, param_list: list[ParameterValue], param_def: list[ParameterDefinition]):
        self.connect()
        if self.query_name == '':
            logging.warning("Query name must not be empty")
            PopupWindow("Query name must not be empty")
        param_def = sorted(param_def)
        paramDict = {}
        for param in param_list:
            if param_def[param.index].defined_type == ParameterType.File:
                file = open(param.value, 'r')
                filereader = csv.reader(file)
                try:
                    lines = []
                    for line in filereader:
                            lines.append(line[0].strip())
                except Exception as e:
                    PopupWindow(e)
                    raise e
                paramDict[param_def[param.index].arg_name] = lines
            else:
                paramDict[param_def[param.index].arg_name] = param.value
        logging.info("Splitting up commands...")

        commands = [x.strip() for x in script.split(';')]
        try:
            commands.remove("")
        except:
            pass

        logging.info("Script broken into %s commands", len(commands))

        for i, command in enumerate(commands):
            logging.info("Executting command %s", i)
            mergedCommand = self.cursor.mogrify(command, paramDict)
            self.cursor.execute(mergedCommand)
            logging.info("Command executed sucessfully.")
        
        logging.info("Query Excecuted Successfully.")
        self.disconnect()
        return 0

    def saveResults(self, outfile_name: str):
        logging.info("Saving Query Results...")
        if outfile_name.find('.') == -1:
            outpath = f"{os.getenv('output_filepath')}/{outfile_name}.tsv"
        else:
            outpath = f"{os.getenv('output_filepath')}/{outfile_name}"

        try:
            with open(outpath, 'w', encoding="utf-8") as out:
                for i, column in enumerate(self.cursor.description):
                    out.write(column[0])
                    if i != len(self.cursor.description)-1:
                        out.write('\t')
                out.write('\n')
                for line in self.cursor.fetchall(): 
                    newline = ""
                    for item in line:
                        if newline != "":
                            newline += "\t"
                        newline += str(item)
                    out.write((newline+'\n').replace('\'', ''))
        except Exception as e:
            raise e
        logging.info(f"Query Results Saved Sucessfully as \"{outfile_name}.\"\n")


# Popup Windows to give alert notices
class PopupWindow:
    def __init__(self, text):
        self.popup = tk.Tk()
        self.popup.attributes("-topmost", True)
        self.popup.configure(background="lavender")
        self.popup.wm_title("Popup Notice")

        self.text_label = ttk.Label(master=self.popup, text=text, font='TkDefaultFont 10 bold',background="lavender",justify="center")
        self.text_label.pack(side="top", anchor="center", pady=5, padx=5)
        self.close_button = tk.Button(master=self.popup, text="OK", font='TkDefaultFont 10 bold', command=self.close)
        self.close_button.pack(side="top", anchor="center",pady=5)

        self.popup.mainloop()

    def close(self):
        self.popup.destroy()

# Allows query selection
# Includes buttons to open the query display and to run the query

class ActionMenu:
    def __init__(self, querier, script_files):
        logging.info("Initializing Action Menu...")

        self.querier = querier
        self.script_files = script_files
        self.script = ""

        self.act_menu = tk.Tk()
        self.act_menu.attributes("-topmost", True)
        self.act_menu.configure(background="lavender")
        sv_ttk.set_theme("light")

        self.act_menu.wm_title("LDPlite Querier - Actions Menu")

        # General Title
        self.title = ttk.Label(master=self.act_menu, text="Select a query and input a file name.", font='TkDefaultFont 12 bold')
        self.title.configure(background="lavender")
        #self.title.grid(row=0, column=0, columnspan=3)
        self.title.pack(side='top', anchor='center', pady=5)
        

        # Selected Query Label
        self.query_desc = ttk.Label(master=self.act_menu, text="Query Name: ", font='TkDefaultFont 10 bold')
        self.query_desc.configure(background="lavender")
        #self.query_desc.grid(row=1, column=0)
        self.query_desc.pack(side='top')

        # Query Select Dropdown
        options = self.script_files.list_script_files()
        self.config_input_options = ttk.Combobox(self.act_menu, value=options, width=45)
        self.config_input_options.bind("<<ComboboxSelected>>", self.querySelected)
        #self.config_input_options.grid(row=1, column=1, columnspan=2)
        self.config_input_options.pack(fill='x', side='top', padx=15, pady=5)

        # Output File Name Prompt
        self.file_desc = ttk.Label(master=self.act_menu, text="Output File Name:", font='TkDefaultFont 10 bold')
        self.file_desc.configure(background="lavender")
        #self.file_desc.grid(row=3, column=0, columnspan=1)
        self.file_desc.pack(side='top')

        # Output File Name Field
        # Defaults to the name of the query file
        self.file_prompt = ttk.Entry(master=self.act_menu, font='TkDefaultFont 10', width=41)
        self.file_prompt.insert(0, querier.query_name)
        #self.file_prompt.grid(row=3, column=1, columnspan=2)
        self.file_prompt.pack(side='top', fill='x', padx=15, pady=5)

        # Run Query Button
        self.run = tk.Button(master=self.act_menu, text="Run Query", command=self.run_query, font='TkDefaultFont 10 bold')
        #self.run.grid(row=4, column=1, columnspan=1)
        self.run.pack(side='bottom', pady=10)

        # Menu Bar
        # File>Exit and File>Reconfigure
        self.main_menu_bar = tk.Menu(master=self.act_menu)
        self.file_menu = tk.Menu(master=self.main_menu_bar, tearoff=0)
        self.file_menu.add_command(label="Exit", command=sys.exit)
        self.main_menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.act_menu.config(menu=self.main_menu_bar)

        # Param Header Label
        self.param_header = ttk.Label(master=self.act_menu, text="Input Query Parameters:", font='TkDefaultFont 11 bold')
        self.param_header.configure(background="lavender")
        self.param_active = False

        # List to hold parameter objects
        self.param_objects = []


        logging.info("Action Menu Initialized.\n")

        self.act_menu.mainloop()
        
    # Loads the selected query. Updates menu to display the parameters for the query and auto-fills the output file name field.
    def querySelected(self, *args):
        logging.info(f"Query \"{self.config_input_options.get()}\" selected.")
        if self.param_active:
            self.param_header.pack_forget()
            self.param_active = False
        try:
            for item in self.param_objects:
                item['label'].destroy()
                item['entry'].destroy()
        except Exception as e:
            winsound.MessageBeep()
            logging.warning(e.with_traceback.__dict__)
            PopupWindow(e)        
        self.param_objects.clear()

        self.querier.query_name = self.config_input_options.get()
        self.script = self.script_files.read_script_file(self.querier.query_name)
        try:
            params = parameterized_scripts.get_parameters(self.script)
        except Exception as e:
            logging.warning(e.with_traceback)
            winsound.MessageBeep()
            PopupWindow(e)
        self.file_prompt.delete(0,len(self.file_prompt.get()))
        today = datetime.today()
        self.file_prompt.insert(0, f'{self.querier.query_name[:-4]}--{today.day}-{today.month}-{today.year}--{today.hour}-{today.minute}-{today.second}.tsv')
        if params != []:
            self.param_header.pack(pady=5)
            self.param_active = True
        for param in params:
            logging.info(f"Creating Query Parameter Labels and Entries for parameter {param.index}: {param.description}")
            if param.defined_type == ParameterType.Text:
                label = ttk.Label(master=self.act_menu, text=param.description, font='TkDefaultFont 10 bold')
                label.configure(background="lavender")
                entry = ttk.Entry(master=self.act_menu, font='TkDefaultFont 10', width=41)
                if param.default is not None:
                    entry.insert(0, param.default)
                self.param_objects.append({"label": label,"entry": entry, "value":param.default, "definition": param})

            elif param.defined_type == ParameterType.Date:
                label = ttk.Label(master=self.act_menu, text=param.description, font='TkDefaultFont 10 bold')
                label.configure(background="lavender")
                entry = DateEntry(master=self.act_menu, width=45, date_pattern="YYYY-MM-DD")
                if param.default is not None:
                    entry.set_date(param.default)
                self.param_objects.append({"label": label, "entry": entry, "value":param.default, "definition":param})

            elif param.defined_type == ParameterType.File:
                label = ttk.Label(master=self.act_menu, text=param.description, font='TkDefaultFont 10 bold')
                label.configure(background="lavender")
                index = param.index
                entry = tk.Button(master=self.act_menu, text="Select File", command= lambda: self.file_select(index), font='TkDefaultFont 10 bold', width=30)
                self.param_objects.append({"label": label, "entry": entry, "value":param.default, "definition": param})

            elif param.defined_type == ParameterType.Dropdown:
                label = ttk.Label(master=self.act_menu, text=param.description, font='TkDefaultFont 10 bold')
                label.configure(background="lavender")
                entry = ttk.Combobox(self.act_menu, values=param.selectable_values, width=45, height=4)
                if param.default is not None:
                    entry.set(param.default)
                self.param_objects.append({"label": label,"entry": entry, "value":param.default, "definition": param})

            self.param_objects[param.index]["label"].pack(side='top')
            self.param_objects[param.index]["entry"].pack(side='top',pady=5)

    # Allows the user to select a file when a query uses the "SINGLE_COLUMN_CSV_NO_HEADER" parameter option
    # Param index identifies which parameter is being entered
    def file_select(self, param_index):
        
        logging.info("Opening file Select dialogue for parameter %s", param_index)
        filename = tk.filedialog.askopenfilename()
        if not filename:
            logging.warning("Selected file not found.")
            PopupWindow("Selected file not found.")
            return
        
        self.param_objects[param_index]["entry"].config(text = filename[filename.rfind('/')+1:])
        self.param_objects[param_index]['value'] = filename
        self.param_objects[param_index]["label"].update_idletasks()

        self.run.config(state="normal")
        logging.info("File selected")
        
    # Tells the querier to execute the query. Triggers the save function
    def run_query(self):
        paramValues = []
        paramDefinitions = []
        for param in self.param_objects:
            if isinstance(param['entry'], tk.Button):
                paramValues.append(ParameterValue(index=param['definition'].index, description=param['definition'].description, value=str(param['value'])))
            else:
                paramValues.append(ParameterValue(index=param['definition'].index, description=param['definition'].description, value=param['entry'].get()))
            paramDefinitions.append(param['definition'])

        logging.info("Parameter values: %s", paramValues)
        paramValidation = parameterized_scripts.validate_parameters(self.script, paramValues)
        popupMessage = 'Parameter Validation Errors:\n'
        if len(paramValidation) > 0:
            for validation in paramValidation:
                popupMessage += "\n"
                for param in self.param_objects:
                    if validation.index == param["definition"].index:
                        popupMessage += f"{param['definition'].description} -- {validation.message}"
            popupMessage += "\n"
            logging.warning(paramValidation)
            PopupWindow(popupMessage)

        file = self.file_prompt.get()
        try:
            self.querier.runQuery(self.script, paramValues, paramDefinitions)
            self.querier.saveResults(file)
        except Exception as e:
            logging.warning(e.with_traceback)
            self.querier.rollbackTransaction()
            winsound.MessageBeep()
            PopupWindow(e)
            return
        winsound.MessageBeep()
        logging.info(f"Query Results Saved as:\n\n{file}")
        PopupWindow(f"Query Results Saved as:\n\n{file}")

def launch():
    try:
        try:            
            os.mkdir(os.getenv('query_filepath'))
            logging.info(f"Directory for queries \"{os.getenv('query_filepath')}\" created\n")
        except Exception as e:
            logging.info("Existing query directory found\n")
        try:
            os.mkdir(os.getenv('output_filepath'))
            logging.info(f"Directory for outputted files \"{os.getenv('output_filepath')}\" created\n")
        except Exception as e:
            logging.info("Existing output directory found\n")

    except Exception as e:
        logging.warning(e.with_traceback)
        winsound.MessageBeep()
        PopupWindow(e)
        return

    try:
        querier = Querier()
    except Exception as e:
        logging.warning(e.with_traceback)
        winsound.MessageBeep()
        PopupWindow(e)
        return
    
    script_files = ScriptFiles(os.path.abspath(os.getenv('query_filepath')))
    ActionMenu(querier=querier, script_files=script_files)

if __name__ == "__main__":
    dotenv.load_dotenv()

    try:
        os.mkdir(os.getenv('log_file_output_filepath'))
        print(f"Directory for logs \"{os.getenv('log_file_output_filepath')}\" created")
    except Exception as e:
        print("Existing log directory found")

    start_time = datetime.now()
    logFile = f'{os.getenv("log_file_output_filepath")}/LDlite Reporting - {start_time.year}-{start_time.month}-{start_time.day}--{start_time.hour}-{start_time.minute}-{start_time.second}.log'
    logging.basicConfig(filename=logFile, encoding='utf-8', level=logging.DEBUG,
                    format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
    logging.info("Beginning Log")
    
    launch()