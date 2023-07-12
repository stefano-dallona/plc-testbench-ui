param(
     [Parameter()]
     [string]$EnvFile
 )

Invoke-Command -ScriptBlock {
  Get-Content $EnvFile | ForEach-Object {
    $name, $value = $_.split('=')
    if (-Not ([string]::IsNullOrWhiteSpace($name) -Or $name -clike '#*')) {
      #Write-Host "$name=$value"
      Set-Content env:\$name $value
    }
  }
  #Set-Content env:\VAR1 VAL1
  ./env/Scripts/activate
  #python -c "import os; print(os.environ['VAR1']);"
  python app.py
}
