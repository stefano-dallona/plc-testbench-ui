#powershell.exe -noprofile -executionpolicy bypass -file C:\tmp\launch-with-env.ps1 -EnvFile prova.env gci env:*

param(
  [Parameter(Mandatory)]
  [string]$EnvFile,

  [parameter(
    mandatory = $true,
    valueFromRemainingArguments = $true
  )]
  [string[]]$PassthroughArguments
)
 
Invoke-Command -ScriptBlock {
  Get-Content $EnvFile | ForEach-Object {
    $name, $value = $_.split('=')
    if (-Not ([string]::IsNullOrWhiteSpace($name) -Or $name -clike '#*')) {
      Write-Host "$name=$value"
      Set-Content env:\$name $value
      Set-Variable -Name $name -Value $value -Scope global
    }
  }
  write-host "EnvFile=$EnvFile, PassthroughCommand=($PassthroughArguments)"
  $command=$ExecutionContext.InvokeCommand.ExpandString($PassthroughArguments)
  write-host "command=$command"
  Invoke-Expression $ExecutionContext.InvokeCommand.ExpandString($PassthroughArguments)
}
  
