# 콘솔 출력 인코딩을 UTF-8로 설정
# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 현재 스크립트 위치를 기준으로 작업 디렉토리 설정
# Set working directory to script location
$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

# 1. 최신 의존성 설치
# 1. Install latest dependencies
Write-Host "[1/4] Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 2. 실행 파일 빌드 (PyInstaller & Manifest 생성)
# 2. Build executable (PyInstaller & Manifest generation)
Write-Host "`n[2/4] Building executable..." -ForegroundColor Yellow
python build.py

# 3. 빌드된 파일을 패키징 폴더로 복사
# 3. Copy built file to packaging folder
Write-Host "`n[3/4] Copying executable..." -ForegroundColor Yellow
if (-not (Test-Path "store_package")) {
    New-Item -ItemType Directory -Force -Path "store_package"
}
Copy-Item "dist\GodModTimer.exe" -Destination "store_package\GodModTimer.exe" -Force

# 4. MSIX 패키징 (MakeAppx 자동 검색 및 실행)
# 4. MSIX Packaging (Auto-detect MakeAppx and run)
$makeappx = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter "MakeAppx.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName -First 1

if ($makeappx) {
    Write-Host "`n[4/4] Running MakeAppx..." -ForegroundColor Green
    
    $sourceDir = Join-Path $ScriptDir "store_package"
    $outputFile = Join-Path $ScriptDir "GodModTimer.msix"
    
    & $makeappx pack /d "$sourceDir" /p "$outputFile" /o
    
    if ($?) { 
        Write-Host "`nSUCCESS: Packaging successful! File created at:" -ForegroundColor Cyan 
        Write-Host "   $outputFile" -ForegroundColor Cyan
    }
} else {
    Write-Host "`nERROR: MakeAppx.exe not found. Please check Windows SDK installation." -ForegroundColor Red
}