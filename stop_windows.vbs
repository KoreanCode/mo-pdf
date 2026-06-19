Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

command = "cmd.exe /c " & Chr(34) & fso.BuildPath(scriptDir, "stop_windows.bat") & Chr(34)
shell.Run command, 1, False
