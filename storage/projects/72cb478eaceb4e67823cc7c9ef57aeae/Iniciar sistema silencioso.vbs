Option Explicit

Dim shell, fileSystem, projectFolder, logFile, appFile, commandLine, attempt
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

projectFolder = fileSystem.GetParentFolderName(WScript.ScriptFullName)
appFile = projectFolder & "\app.py"
logFile = projectFolder & "\dados\servidor.log"
shell.CurrentDirectory = projectFolder

If Not ServerReady() Then
    commandLine = "cmd.exe /d /c " & Quote("py -3 " & Quote(appFile) & " >> " & Quote(logFile) & " 2>&1")
    shell.Run commandLine, 0, False
End If

For attempt = 1 To 90
    If ServerReady() Then
        shell.Run "http://localhost:8000", 1, False
        WScript.Quit 0
    End If
    WScript.Sleep 1000
Next

WriteLog "Servidor não respondeu após 90 segundos; o navegador não foi aberto."
WScript.Quit 1

Function ServerReady()
    On Error Resume Next
    Dim request
    Set request = CreateObject("WinHttp.WinHttpRequest.5.1")
    If Err.Number <> 0 Then
        Err.Clear
        ServerReady = False
        Exit Function
    End If
    request.SetTimeouts 300, 300, 500, 500
    request.Open "GET", "http://127.0.0.1:8000/api/me", False
    request.Send
    If Err.Number = 0 Then
        ServerReady = (request.Status = 200)
    Else
        ServerReady = False
    End If
    Err.Clear
    Set request = Nothing
    On Error GoTo 0
End Function

Sub WriteLog(message)
    On Error Resume Next
    Dim log
    Set log = fileSystem.OpenTextFile(logFile, 8, True)
    log.WriteLine Now & " INFO " & message
    log.Close
    On Error GoTo 0
End Sub

Function Quote(value)
    Quote = Chr(34) & value & Chr(34)
End Function
