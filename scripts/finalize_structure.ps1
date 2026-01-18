# 프로젝트 구조 최종 정리 스크립트

$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

# 1. scripts 폴더 확인
if (-not (Test-Path "scripts")) {
    New-Item -ItemType Directory -Force -Path "scripts" | Out-Null
}

# 2. create_assets.py 이동 (root 또는 src -> scripts)
if (Test-Path "create_assets.py") {
    Move-Item -Path "create_assets.py" -Destination "scripts/create_assets.py" -Force
    Write-Host "🚚 Moved create_assets.py to scripts/" -ForegroundColor Cyan
}
elseif (Test-Path "src/create_assets.py") {
    Move-Item -Path "src/create_assets.py" -Destination "scripts/create_assets.py" -Force
    Write-Host "🚚 Moved src/create_assets.py to scripts/" -ForegroundColor Cyan
}

# 3. 루트의 관리용 스크립트들을 scripts 폴더로 이동
# (clean.ps1 추가)
$adminScripts = @("refine_structure.ps1", "reorganize.ps1", "clean.ps1")
foreach ($script in $adminScripts) {
    if (Test-Path $script) {
        Move-Item -Path $script -Destination "scripts/$script" -Force
        Write-Host "🚚 Moved $script to scripts/" -ForegroundColor Cyan
    }
}

# 4. tests 폴더 생성 (테스트 코드용)
if (-not (Test-Path "tests")) {
    New-Item -ItemType Directory -Force -Path "tests" | Out-Null
    Write-Host "📂 'tests' directory created." -ForegroundColor Green
}

# 5. 자기 자신(finalize_structure.ps1)도 scripts 폴더로 이동
$self = $MyInvocation.MyCommand.Path
if (Test-Path $self) {
    Move-Item -Path $self -Destination "scripts/" -Force
    Write-Host "🚚 Moved finalize_structure.ps1 to scripts/" -ForegroundColor Cyan
}

Write-Host "`n✅ Final structure cleanup complete!" -ForegroundColor Green