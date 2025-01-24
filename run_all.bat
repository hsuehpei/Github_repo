@echo off
set CSVfile_path=C:\Users\admin\Downloads\all_repositories.csv
set XLSXfile_path=C:\Users\admin\Desktop\OPO\Github_fork\history_file\permission\all_repositories.xlsx

for /f "skip=1 tokens=1" %%a in ('wmic os get localdatetime') do (
    set datetime=%%a
    goto :done
)

:done
set ymd=%datetime:~0,8%
set today=%ymd%

:: 將後端日誌文件名設置為包含日期
set backend_log_file=history_log\backend_%today%.log


rem 啟動伺服器
cd C:\Users\admin\Desktop\OPO\Github_fork\Backend
start cmd /k "npm run start 1>> %backend_log_file% 2>>&1" 
rem 等待 10 秒讓伺服器啟動
timeout /t 10
cd C:\Users\admin\Desktop\OPO\Github_fork\Frontend
start run.bat
rem 等待 10 秒讓伺服器啟動
timeout /t 10
rem bowser open
cd C:\Users\admin\Desktop\OPO\Github_fork
set log_file=history_file\log\github_fork_%today%.log

python downloadCSV.py

set download_status=%errorlevel%
rem check Python script return value
if %download_status% neq 0 (
    echo download failed, running tg_alert.py
    goto :end
)

echo start converting csv to xlsx
python convertToXlsx.py

set convert_status=%errorlevel%
if %convert_status% neq 0 (
    echo convert failed, running tg_alert.py
    goto :end
)

echo start add department
python getDeptByName.py

set department_status=%errorlevel%
if %department_status% neq 0 (
    echo convert failed, running tg_alert.py
    goto :end
)

echo start upload xlsx to onedrive
python upLoadToOnedrive.py

set upload_status=%errorlevel%
if %upload_status% neq 0 (
    echo upload failed, running tg_alert.py
    goto :end
)

rem CSV and XLSX cleanup and rename
if exist %CSVfile_path% (
    if exist %XLSXfile_path% (
        del %CSVfile_path%
        echo successfully deleted
    ) else (
        echo XLSX file not found
    )
) else (
    echo CSV file not found
)

echo rename xlsx file
python changeXlsxName.py
goto :end

:end
rem 最後一定會執行這一步，通知完成
python tg_alert.py %log_file%

taskkill /F /IM cmd.exe /T
taskkill /F /IM conhost.exe /T


