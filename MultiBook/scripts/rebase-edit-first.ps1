$path = $args[0]
$c = Get-Content $path
$c[-1] = $c[-1] -replace '^pick', 'edit'
$c | Set-Content $path
