# 프로젝트 구조 추가 개선 스크립트
# 유틸리티 스크립트들을 scripts 폴더로 정리합니다.

$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

# 1. scripts 디렉토리 생성
if (-not (Test-Path "scripts")) {
    New-Item -ItemType Directory -Force -Path "scripts" | Out-Null
    Write-Host "📂 'scripts' directory created." -ForegroundColor Green
}

# 2. 파일 이동 및 정리
if (Test-Path "reorganize.ps1") {
    Move-Item -Path "reorganize.ps1" -Destination "scripts" -Force
    Write-Host "🚚 Moved reorganize.ps1 to scripts/" -ForegroundColor Cyan
}

if (Test-Path "create_assets.py") {
    Remove-Item -Path "create_assets.py" -Force
    Write-Host "🗑️  Removed old create_assets.py (replaced with new version in scripts/)" -ForegroundColor Yellow
}

Write-Host "`n✅ Structure refinement complete!" -ForegroundColor Green