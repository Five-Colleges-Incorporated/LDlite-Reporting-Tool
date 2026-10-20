pyinstaller --onefile --windowed ./src/main.py -n LDliteSingleSelect --distpath "%cd%" --workpath exe_build --noconfirm
del LDliteSingleSelect.spec
rmdir /Q /S exe_build
pause
