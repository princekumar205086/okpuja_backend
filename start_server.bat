@echo off
echo Starting Django Development Server...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run Django check
echo Running Django check...
python manage.py check
if %errorlevel% neq 0 (
    echo.
    echo ❌ Django check failed!
    pause
    exit /b 1
)

echo.
echo ✅ Django check passed!
echo.

REM Create migrations if needed
echo Creating migrations...
python manage.py makemigrations
if %errorlevel% neq 0 (
    echo.
    echo ❌ Migration creation failed!
    pause
    exit /b 1
)

echo.
echo Running migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo.
    echo ❌ Migration failed!
    pause
    exit /b 1
)

echo.
echo ✅ Database setup complete!
echo.

REM Start server
echo Starting development server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver 0.0.0.0:8000

pause
