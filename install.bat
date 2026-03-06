@echo off
echo Installing Python dependencies...
python -m pip install -r requirements.txt
echo.
echo Initializing database with test data...
python init_db.py
echo.
echo Starting the application...
python app.py
pause
