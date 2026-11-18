"""A local interface for executing parameterized SQL queries."""

import logging
import os
import sys
import tkinter as tk
import winsound
from datetime import datetime
from pathlib import Path
from tkinter import EventType, filedialog, ttk

import sv_ttk
from tkcalendar import DateEntry

from .adapters.output_file import LocalOutputFile
from .adapters.postgres import PostgresDB
from .adapters.script_files import ScriptFiles
from .handlers import Handlers
from .parameterized_scripts import ParameterType, ParameterValue

logger = logging.getLogger(__name__)


class PopupWindow:
    """Popup Window to display alert messages.

    Attributes:
    ----------
    popup : Tk
        The root application for the message window.
    text_label : ttk.Label
        The popup message text.
    close_button : tk.Button
        The button to close the window.

    Methods:
    -------
    close() -> None
        Destroys the popup window.
    """

    def __init__(self, text: str) -> None:
        """Initialize and open popup window displaying the supplied text.

        Args:
            text (str): The popup message text.
        """
        self.popup = tk.Tk()
        self.popup.attributes("-topmost", True)
        self.popup.configure(background="lavender")
        self.popup.wm_title("Popup Notice")

        self.text_label = ttk.Label(
            master=self.popup,
            text=text,
            font="TkDefaultFont 10 bold",
            background="lavender",
            justify="center",
        )
        self.text_label.pack(side="top", anchor="center", pady=5, padx=5)
        self.close_button = tk.Button(
            master=self.popup,
            text="OK",
            font="TkDefaultFont 10 bold",
            command=self.close,
        )
        self.close_button.pack(side="top", anchor="center", pady=5)

        self.popup.mainloop()

    def close(self) -> None:
        """Destroys the popup window."""
        self.popup.destroy()


class ActionMenu:
    """The program's primary program window.

    Attributes:
    ----------
    handlers : Handlers
        The handlers responsible for loading, selecting, and executing queries.
    act_menu : tk.Tk
        The root application for the primary window.
    title : ttk.Label
        The text prompting the user to select a query and set an output file name.
    query_desc : ttk.Label
        The label for the query selection dropdown.
    config_input_options : ttk.Combobox
        The query selection dropdown.
    file_desc : ttk.Label
        The label for the output file name field.
    output_file_prompt : ttk.Entry
        The output field name field.
    run : tk.Button
        The button to excecute the selected query.
    main_menu_bar : tk.Menu
        The top menu bar.
    file_menu : tk.Menu
        The File dropdown in the top menu bar.
    param_header : ttk.Label
        The text prompting the user to input parameter values.
    param_active : bool
        Indicates if the selected query includes parameters
    param_objects : list
        The list of the selected query's parameter fields and their labels

    Methods:
    -------
    query_selected(*args: tuple) -> None
        Updates output file name and displays parameters when a query is selected.
    file_select(param_index) -> None
        Opens the file dialog for SINGLE_COLUMN_CSV_NO_HEADER parameters.
    run_query() -> None
        Executes the selected query.
    """

    def __init__(self, handlers: Handlers) -> None:
        """Initialize the primary program window."""
        logger.info("Initializing Action Menu...")

        self.handlers = handlers

        # Root
        self.act_menu = tk.Tk()
        self.act_menu.attributes("-topmost", True)
        self.act_menu.configure(background="lavender")
        sv_ttk.set_theme("light")
        self.act_menu.wm_title("LDPlite Querier - Actions Menu")

        # General Title
        self.title = ttk.Label(
            master=self.act_menu,
            text="Select a query and input a file name.",
            font="TkDefaultFont 12 bold",
        )
        self.title.configure(background="lavender")
        self.title.pack(side="top", anchor="center", pady=5)

        # Selected Query Label
        self.query_desc = ttk.Label(
            master=self.act_menu, text="Query Name: ", font="TkDefaultFont 10 bold"
        )
        self.query_desc.configure(background="lavender")
        self.query_desc.pack(side="top")

        # Query Select Dropdown
        options = self.handlers.handle_page_load()
        if len(options) == 0:
            msg = "Queries directory contains no .sql files"
            PopupWindow(msg)
            raise FileNotFoundError(msg)
        self.config_input_options = ttk.Combobox(
            self.act_menu, values=options, width=45
        )
        self.config_input_options.bind("<<ComboboxSelected>>", self.query_selected)
        self.config_input_options.pack(fill="x", side="top", padx=15, pady=5)

        # Output File Name Label
        self.file_desc = ttk.Label(
            master=self.act_menu, text="Output File Name:", font="TkDefaultFont 10 bold"
        )
        self.file_desc.configure(background="lavender")
        self.file_desc.pack(side="top")

        # Output File Name Field
        self.output_file_prompt = ttk.Entry(
            master=self.act_menu, font="TkDefaultFont 10", width=41
        )
        self.output_file_prompt.pack(side="top", fill="x", padx=15, pady=5)

        # Run Query Button
        self.run = tk.Button(
            master=self.act_menu,
            text="Run Query",
            command=self.run_query,
            font="TkDefaultFont 10 bold",
        )
        self.run.pack(side="bottom", pady=10)

        # Menu Bar
        # File>Exit
        self.main_menu_bar = tk.Menu(master=self.act_menu)
        self.file_menu = tk.Menu(master=self.main_menu_bar, tearoff=0)
        self.file_menu.add_command(label="Exit", command=sys.exit)
        self.main_menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.act_menu.config(menu=self.main_menu_bar)

        # Param Header Label
        self.param_header = ttk.Label(
            master=self.act_menu,
            text="Input Query Parameters:",
            font="TkDefaultFont 11 bold",
        )
        self.param_header.configure(background="lavender")
        self.param_active = False

        # List to hold parameter objects
        self.param_objects = []

        logger.info("Action Menu Initialized.\n")

        self.act_menu.mainloop()

    def query_selected(self, *args: tuple[EventType]) -> None:
        """Loads the selected query and creates input fields for its parameters."""
        logger.info('Query "%s" selected.', self.config_input_options.get())
        if self.param_active:
            self.param_header.pack_forget()
            self.param_active = False

        for item in self.param_objects:
            item["label"].destroy()
            item["entry"].destroy()

        self.param_objects.clear()

        query_name = self.config_input_options.get()

        try:
            params = self.handlers.handle_script_selected(query_name)
        except (ValueError, FileNotFoundError) as e:
            logger.warning(e.args[0])
            winsound.MessageBeep()
            PopupWindow(str(e.args[0]))
            return
        self.output_file_prompt.delete(0, len(self.output_file_prompt.get()))
        today = datetime.today()
        self.output_file_prompt.insert(
            0,
            f"{query_name[:-4]}--{today.day}-{today.month}-{today.year}--{today.hour}-{today.minute}-{today.second}.tsv",
        )
        if params != []:
            self.param_header.pack(pady=5)
            self.param_active = True
        for param in params:
            logger.info(
                "Creating Query Parameter Labels and Entries for parameter %s: %s",
                param.index,
                param.description,
            )
            if param.defined_type == ParameterType.Text:
                label = ttk.Label(
                    master=self.act_menu,
                    text=param.description,
                    font="TkDefaultFont 10 bold",
                )
                label.configure(background="lavender")
                entry = ttk.Entry(
                    master=self.act_menu, font="TkDefaultFont 10", width=41
                )
                if param.default is not None:
                    entry.insert(0, param.default)
                self.param_objects.append(
                    {
                        "label": label,
                        "entry": entry,
                        "value": param.default,
                        "definition": param,
                    }
                )

            elif param.defined_type == ParameterType.Date:
                label = ttk.Label(
                    master=self.act_menu,
                    text=param.description,
                    font="TkDefaultFont 10 bold",
                )
                label.configure(background="lavender")
                entry = DateEntry(
                    master=self.act_menu, width=45, date_pattern="YYYY-MM-DD"
                )
                if param.default is not None:
                    entry.set_date(param.default)
                self.param_objects.append(
                    {
                        "label": label,
                        "entry": entry,
                        "value": param.default,
                        "definition": param,
                    }
                )

            elif param.defined_type == ParameterType.File:
                label = ttk.Label(
                    master=self.act_menu,
                    text=param.description,
                    font="TkDefaultFont 10 bold",
                )
                label.configure(background="lavender")
                entry = tk.Button(
                    master=self.act_menu,
                    text="Select File",
                    font="TkDefaultFont 10 bold",
                    width=30,
                )
                entry.bind(
                    "<ButtonPress>", lambda event, x=param.index: self.file_select(x)
                )
                entry.bind("<Leave>", lambda event, e=entry: e.config(relief="raised"))
                self.param_objects.append(
                    {
                        "label": label,
                        "entry": entry,
                        "value": param.default,
                        "definition": param,
                    }
                )

            elif param.defined_type == ParameterType.Dropdown:
                label = ttk.Label(
                    master=self.act_menu,
                    text=param.description,
                    font="TkDefaultFont 10 bold",
                )
                label.configure(background="lavender")
                entry = ttk.Combobox(
                    self.act_menu, values=param.selectable_values, width=45, height=4
                )
                if param.default is not None:
                    entry.set(param.default)
                self.param_objects.append(
                    {
                        "label": label,
                        "entry": entry,
                        "value": param.default,
                        "definition": param,
                    }
                )

            self.param_objects[param.index]["label"].pack(side="top")
            self.param_objects[param.index]["entry"].pack(side="top", pady=5)

    def file_select(self, param_index: int) -> None:
        """Opens the file dialog for SINGLE_COLUMN_CSV_NO_HEADER parameters."""
        logger.info("Opening file Select dialogue for parameter %s", param_index)
        filename = filedialog.askopenfilename()
        if not filename:
            logger.warning("Selected file not found.")
            PopupWindow("Selected file not found.")
            return

        self.param_objects[param_index]["entry"].config(
            text=filename[filename.rfind("/") + 1 :]
        )
        self.param_objects[param_index]["value"] = filename
        self.param_objects[param_index]["label"].update_idletasks()

        self.run.config(state="normal")
        logger.info("File selected")

    def run_query(self) -> None:
        """Tells the querier to execute the query. Triggers the save function."""
        param_values = []
        script_file = self.config_input_options.get()
        output_file = self.output_file_prompt.get()

        for param in self.param_objects:
            if isinstance(param["entry"], tk.Button):
                param_values.append(
                    ParameterValue(
                        index=param["definition"].index,
                        description=param["definition"].description,
                        value=str(param["value"]),
                    )
                )
            else:
                param_values.append(
                    ParameterValue(
                        index=param["definition"].index,
                        description=param["definition"].description,
                        value=param["entry"].get(),
                    )
                )
        logger.info("Parameter values: %s", param_values)
        try:
            results = self.handlers.handle_script_submitted(
                outfile_name=output_file, script_name=script_file, values=param_values
            )
        except Exception as e:
            logger.warning(e.with_traceback)
            PopupWindow(str(e))
            return
        if len(results) > 0:
            logger.warning("Parameter validation encountered one or more errors.")
            popup_message = "Parameter Validation Errors:\n"
            for error in results:
                popup_message += "\n"
                logger.warning(error.args[0])
                popup_message += error.args[0]
            PopupWindow(popup_message)
        else:
            logger.info("Query Results Saved as:\n\n%s", output_file)
            PopupWindow(f"Query Results Saved as:\n\n{output_file}")


def launch() -> None:
    """Reads environmental variables and initializes the ActionMenu."""
    Path(os.getenv("QUERY_FILEPATH", "")).mkdir(parents=True, exist_ok=True)
    Path(os.getenv("OUTPUT_FILEPATH", "")).mkdir(parents=True, exist_ok=True)
    outfile = LocalOutputFile(os.getenv("OUTPUT_FILEPATH", ""))
    script_files = ScriptFiles(os.getenv("QUERY_FILEPATH", ""))

    dbname = os.getenv("DBNAME", "")
    user = os.getenv("USER", "")
    password = os.getenv("PASSWORD", "")
    host = os.getenv("HOST", "")
    port = os.getenv("PORT", "")

    db = PostgresDB(dbname=dbname, user=user, password=password, host=host, port=port)
    handlers = Handlers(output_file_creator=outfile, script_files=script_files, db=db)

    ActionMenu(handlers)
