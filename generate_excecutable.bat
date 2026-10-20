pyinstaller --onefile --windowed ./src/ldlite_reporting_tool/LDliteSingleSelect.py -n LDliteSingleSelect --distpath "%cd%" --workpath exe_build --noconfirm
del LDliteSingleSelect.spec
rmdir /Q /S exe_build
pause
