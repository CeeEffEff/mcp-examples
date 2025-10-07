# Development Environment Setup Script for agent-seomax (Windows)
# This script creates a project-specific Python virtual environment and installs all dependencies

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "GCP Digital Twin Agent Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
            Write-Host "Error: Python 3.9 or higher is required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ $pythonVersion found" -ForegroundColor Green
    }
} catch {
    Write-Host "Error: Python not found. Please install Python 3.9 or higher." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Warning: venv directory already exists" -ForegroundColor Yellow
    $response = Read-Host "Remove existing venv and create new one? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Remove-Item -Recurse -Force venv
        python -m venv venv
        Write-Host "✓ New virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "Using existing venv" -ForegroundColor Yellow
    }
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip wheel setuptools
Write-Host "✓ pip upgraded" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "✓ All dependencies installed" -ForegroundColor Green
Write-Host ""

# Create .env from template if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠ Please edit .env and add your configuration" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}
Write-Host ""

# Run basic import test
Write-Host "Verifying installation..." -ForegroundColor Yellow
try {
    python -c "from ingestion_pipeline import graph_queries; print('Import successful')" 2>$null
    Write-Host "✓ Package imports working correctly" -ForegroundColor Green
} catch {
    Write-Host "⚠ Warning: Package imports failed (this is expected if GCP credentials not configured)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Activate the virtual environment:" -ForegroundColor Yellow
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host ""
Write-Host "2. Configure your .env file with GCP credentials"
Write-Host ""
Write-Host "3. Run tests:" -ForegroundColor Yellow
Write-Host "   pytest tests/ -v" -ForegroundColor Green
Write-Host ""
Write-Host "4. Run specific test suite:" -ForegroundColor Yellow
Write-Host "   pytest tests/test_graph_queries.py -v --cov" -ForegroundColor Green
Write-Host ""
Write-Host "To deactivate the virtual environment later:" -ForegroundColor Yellow
Write-Host "   deactivate" -ForegroundColor Green
Write-Host ""
