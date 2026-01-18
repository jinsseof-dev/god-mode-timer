# 프로젝트 구조 개선 스크립트
# 소스 코드를 src 폴더로 이동합니다.

$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

# 1. src 디렉토리 생성
if (-not (Test-Path "src")) {
    New-Item -ItemType Directory -Force -Path "src" | Out-Null
    Write-Host "📂 'src' directory created." -ForegroundColor Green
}

# 2. 소스 파일 이동
$sourceFiles = @("gui.py", "main.py", "utils.py", "common.py", "taskbar.py", "settings_window.py", "stats_window.py")

foreach ($file in $sourceFiles) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination "src" -Force
        Write-Host "🚚 Moved $file to src/" -ForegroundColor Cyan
    }
}

Write-Host "`n✅ Project reorganization complete!" -ForegroundColor Green