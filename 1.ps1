$WinAppsDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
$EnginePath = "$WinAppsDir\1.py"
$CmdPath = "$WinAppsDir\imagehtml.cmd"

if (!(Test-Path -Path $WinAppsDir)) {
    New-Item -ItemType Directory -Force -Path $WinAppsDir | Out-Null
}

$DownloadUrl = "https://raw.githubusercontent.com/YileinaPiFa/1/main/1.py?t=" + [DateTimeOffset]::Now.ToUnixTimeSeconds()
Invoke-WebRequest -Uri $DownloadUrl -OutFile $EnginePath -UseBasicParsing

$CmdContent = "@echo off`npython `"$EnginePath`" %*"
Set-Content -Path $CmdPath -Value $CmdContent -Encoding ASCII

$RegKey = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Environment", $true)
$CurrentPath = $RegKey.GetValue("Path", "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)

$Paths = $CurrentPath -split ";" | Where-Object { $_ -ne "" }
if ($Paths -notcontains $WinAppsDir) {
    $Paths += $WinAppsDir
    $NewPath = $Paths -join ";"
    $RegKey.SetValue("Path", $NewPath, [Microsoft.Win32.RegistryValueKind]::ExpandString)
    
    $Signature = @"
[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
    $User32 = Add-Type -MemberDefinition $Signature -Name "Win32SendMessage" -Namespace "Win32" -PassThru
    $Result = [UIntPtr]::Zero
    $User32::SendMessageTimeout([IntPtr]0xffff, 0x001a, [UIntPtr]::Zero, "Environment", 2, 5000, [ref]$Result) | Out-Null
}
$RegKey.Close()

Write-Host "Done! imagehtml installed successfully." -ForegroundColor Green
