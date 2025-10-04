# install_packages.ps1 - Sequential installation to avoid dependency conflicts
# Run this in PowerShell with venv activated

Write-Host "`n=== Installing Python Packages for Investment Advisor ===" -ForegroundColor Cyan
Write-Host "This will install packages in the correct order to avoid conflicts`n" -ForegroundColor Yellow

# Check if venv is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual environment is activated: $env:VIRTUAL_ENV`n" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: Virtual environment not activated!" -ForegroundColor Red
    Write-Host "Run: .\venv\Scripts\Activate.ps1`n" -ForegroundColor Yellow
    exit
}

# Upgrade pip first
Write-Host "[1/6] Upgrading pip, setuptools, and wheel..." -ForegroundColor Green
python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to upgrade pip!" -ForegroundColor Red
    exit
}

# Install core data processing packages
Write-Host "`n[2/6] Installing core data processing (numpy, pandas)..." -ForegroundColor Green
pip install numpy==1.26.4 pandas==2.2.2 python-dateutil==2.9.0.post0 pytz==2024.1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install core packages!" -ForegroundColor Red
    exit
}

# Install data collection packages
Write-Host "`n[3/6] Installing data collection tools (yfinance, requests)..." -ForegroundColor Green
pip install yfinance==0.2.40 requests==2.32.3 certifi urllib3
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install data collection packages!" -ForegroundColor Red
    exit
}

# Install scientific computing
Write-Host "`n[4/6] Installing scientific computing (scipy, scikit-learn)..." -ForegroundColor Green
pip install scipy==1.14.1 scikit-learn==1.5.2 joblib==1.4.2
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install scientific packages!" -ForegroundColor Red
    exit
}

# Install visualization and technical analysis
Write-Host "`n[5/6] Installing visualization & technical analysis..." -ForegroundColor Green
pip install plotly==5.24.1 matplotlib==3.9.2 pandas-ta==0.3.14b0
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install visualization packages!" -ForegroundColor Red
    exit
}

# Install Streamlit and utilities
Write-Host "`n[6/6] Installing Streamlit and utilities..." -ForegroundColor Green
pip install streamlit==1.39.0 pyyaml==6.0.2 python-dotenv==1.0.1 loguru==0.7.2
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Streamlit!" -ForegroundColor Red
    exit
}

# Verify installation
Write-Host "`n=== Verifying Installation ===" -ForegroundColor Cyan
Write-Host "`nPython Version:" -ForegroundColor Yellow
python --version

Write-Host "`nInstalled Packages:" -ForegroundColor Yellow
pip list | Select-String "streamlit|pandas|numpy|yfinance|scikit|scipy|plotly|pandas-ta"

Write-Host "`n✅ Installation Complete!" -ForegroundColor Green
Write-Host "`nYou can now run your application with:" -ForegroundColor Cyan
Write-Host "  streamlit run app.py" -ForegroundColor White