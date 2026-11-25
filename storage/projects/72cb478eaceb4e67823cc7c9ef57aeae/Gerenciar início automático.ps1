param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Install", "Remove")]
    [string]$Action
)

$ErrorActionPreference = "Stop"
$projectFolder = $PSScriptRoot
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Sistema Biblioteca.lnk"

if ($Action -eq "Remove") {
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath
        Write-Output "Início automático removido."
    } else {
        Write-Output "O início automático já estava desativado."
    }
    exit 0
}

$launcher = Join-Path $projectFolder "Iniciar sistema silencioso.vbs"
if (!(Test-Path -LiteralPath $launcher)) {
    throw "Não foi encontrado o inicializador: $launcher"
}
if (!(Test-Path -LiteralPath (Join-Path $projectFolder "app.py"))) {
    throw "Não foi encontrado app.py em $projectFolder"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:SystemRoot "System32\wscript.exe"
$shortcut.Arguments = '"' + $launcher + '"'
$shortcut.WorkingDirectory = $projectFolder
$shortcut.Description = "Inicia o servidor web do Sistema Biblioteca ao entrar no Windows"
$shortcut.Save()

Write-Output "Início automático configurado para este usuário."
Write-Output "Atalho: $shortcutPath"
Write-Output "O servidor iniciará em segundo plano no próximo acesso ao Windows."
