$WinAppsDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
$EnginePath = "$WinAppsDir\1.py"
$CmdPath = "$WinAppsDir\imagehtml.cmd"

$DownloadUrl = "https://gitee.com/YOUR_USERNAME/imagehtml/raw/main/1.py"
Invoke-WebRequest -Uri $DownloadUrl -OutFile $EnginePath -UseBasicParsing

$CmdContent = "@echo off`npython `"$EnginePath`" %*"
Set-Content -Path $CmdPath -Value $CmdContent -Encoding ASCII

Write-Host "✓ 安装完成！您现在可以在任意终端窗口中输入 imagehtml 使用该工具。" -ForegroundColor Green
