# 프로젝트 청소 스크립트 (빌드 부산물 삭제)

$ScriptDir = $PSScriptRoot
# scripts 폴더 안에 있을 경우를 대비해 상위 경로 확인
if (Split-Path -Leaf $ScriptDir -eq "scripts") {
    $ProjectRoot = Split-Path -Parent $ScriptDir
} else {
    $ProjectRoot = $ScriptDir
}
Set-Location $ProjectRoot

$artifacts = @(
    "build", "dist", "*.spec", "*.pfx", "*.msix", 
    "store_package/*.exe", "store_package/AppxManifest.xml", 
    "app.manifest", "arialbd.ttf", "__pycache__", "src/__pycache__"
)

foreach ($artifact in $artifacts) {
    if (Test-Path $artifact) {
        Remove-Item -Path $artifact -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "🗑️  Removed $artifact" -ForegroundColor Yellow
    }
}
Write-Host "✨ Project cleaned!" -ForegroundColor Green