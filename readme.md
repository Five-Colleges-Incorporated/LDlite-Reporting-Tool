# LDlite Single Select
Copyright (C) 2022-2026  Amelia Sutton

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

See the file "[COPYING](COPYING)" for more details.

## Introduction

An Interface for running simple sql queries without a SQL IDE

## Requirements


* Python 3.10+
* tkinter
* psycopg2
* dotenv
* sv_ttk
* tkcalendar

## Optional Requirements
* pyinstaller


## __Instructions:__

### Setup:

Simplified installation and usage instructions can be found here: https://docs.google.com/document/d/1nGEkgKNdkKOrfOSI5eol9Vj2pLpjtTXabGmMVlcCztw/edit?usp=sharing

* Create .env file in the following format:
> DBNAME= {dbname}
>
> USER= {user}
>
> HOST= {host}
>
> PORT= {port}
>
> PASSWORD= {password}
>
> QUERY_FILEPATH= {query filepath}
>
> OUTPUT_FILEPATH= {output filepath}
>
> LOG_FILE_OUTPUT_FILEPATH= {log filepath}


* **query_filepath,**  **output_filepath,** and **log_file_output_filepath** will be created based on config information in runtime if they do not exist.

* Place any .sql files you wish to run in your **query_filepath** directory.  

* If you need to generate an updated excecutable you only need Python 3.10+ installed. Run **generate_excecutable.bat**. After running, **LDliteSingleSelect.exe** will be up to date. This updates the executable from **LDliteSingleSelect.py** <u>**NOT**</u> from GitHub

### Usage:

* Run the program either by launching **LDliteSingleSelect.exe**, running **LDliteSingleSelect.bat**, or by running **LDliteSingleSelect.py** through the command line.

* Using the dropdown select the **Query Name** for the .sql file you wish to excecute.

* If desired modify the **Output File Name**.

* Enter values for any parameters the query requires.

* Select **Run Query**

* When finished use **File>Exit** to close the program

## Notes
* It is recommended that you use PyInstaller to generate an executable version of LDliteSingleSelect.py to run instead
of running it through LDliteSingleSelect.bat

* See https://github.com/5-C-Folio/LDlite-Queries for a collection of pre-created .sql files
* To create parameters to populate as options in the menu place any prompt text within curly brackets in the value of the desired parameter like so:
`'{Parameter field name}':: VARCHAR AS parameter`
* For date parameters use `'{Parameter field name|DATE}':: VARCHAR AS parameter`
* For a dropdown parameter use `'{Parameter field name|Option 1|Option 2|etc.}':: VARCHAR AS parameter`
* To take in a list of values from a .csv file use `'{Parameter field name|SINGLE_COLUMN_CSV_NO_HEADER}':: VARCHAR AS parameter`

## Contributors


* Amelia Sutton


## Version History

* 0.1
    * Initial Release
* 1.0
    * Full Release
    * Removed **query_file** parameter from the config file in favor of checking for query options in the folder specified by **query_filepath** simplifying the process of adding new queries and removing the need for additional config files.
    * Added **output_filepath** parameter to config
* 1.1
    * Added option to enable a simple logging function
    * Config file now contains two new fields **generate_log,** (Boolean) and **log_file_output_filepath** (String)
* 2.0
  * Logging now uses the logging library **generate_log** configuration parameter removed
  * Added support for new parameter types
    * Date
    * Dropdown
    * List from file
  * Configuration now uses dotenv
  * Changed theme to improve readability

## Known Issues
*
## Planned Features
*
