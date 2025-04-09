function Get-CurrentWeekNumber {
    $currentDate = Get-Date
    $culture = [System.Globalization.CultureInfo]::CurrentCulture
    $weekNumber = $culture.Calendar.GetWeekOfYear($currentDate, $culture.DateTimeFormat.CalendarWeekRule, $culture.DateTimeFormat.FirstDayOfWeek)
    return $weekNumber
}

function Get-DriveName {
    $availabledrives = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    $drives = Get-PSDrive
    foreach($drive in $drives){
        if($drive.name.length -eq 1){
            $availabledrives = $availabledrives.Replace($drive.name, "")
        }
    }
    return $availabledrives[$availabledrives.length - 1]
}

function New-MapSMBShare() {
    param(
        [string]$NetworkPath,
        [string]$DriveName,
        [string]$Username, 
        [securestring]$Password
    )
    $Cred = New-Object System.Management.Automation.PSCredential($Username, $Password)
    New-PSDrive -Name $DriveName -PSProvider FileSystem -Root $NetworkPath -Credential $Cred 
}

# Function to create the backup
function New-BackupZIP() {
    param(
        [Parameter(Mandatory)][string]$fullpath 
    )
    
    $date = Get-Date -Format "yyyyMMddHHmmss"
    $TempZipFile = $fullpath + "\backup_$($env:COMPUTERNAME)_$($date).zip"
    $backuppath = $fullpath + "\WindowsImageBackup"
    # Create the zip file
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory($backuppath, $TempZipFile)
        return $TempZipFile
    }
    catch {
        Write-Error "Error creating backup: $($_.Exception.Message)"
        return $null
    }
}

# Function to send the backup to the API
function Send-BackupToAPI {
    param (
        [string]$ZipFilePath
    )

    if (-not $ZipFilePath) {
        Write-Error "No zip file path provided."
        return $false
    }

    try {
        # Construct the request body (example - adjust based on your API's requirements)
        $body = @{
            file_path = $ZipFilePath
        }

        # Convert the body to JSON
        $jsonBody = $body | ConvertTo-Json

        # Make the API request
        $headers = @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $APIKey" # If your API requires authorization
        }

        $response = Invoke-RestMethod -Uri $APIEndpoint -Method Post -Headers $headers -Body $jsonBody

        # Check the response
        if ($response -is [System.Management.Automation.PSObject]) {
            Write-Host "Backup successfully sent to API. Response: $($response)"
            return $true
        } else {
            Write-Error "Error sending backup to API. Response: $($response)"
            return $false
        }
    }
    catch {
        Write-Error "Error sending backup to API: $($_.Exception.Message)"
        return $false
    }
}


function Remove-MapSMBShare($DriveName) {
    Remove-PSDrive -Name $DriveName -Confirm:$false -Force
}

function New-Backup() {
    param(
        [Parameter(Mandatory)][ValidateSet("0", "1")][string]$UseNetworkShare = (Read-Host "Use Network Share (0=True/1=False)"),
        [string]$BackupDest,
        [string]$Username,
        [securestring]$Password,
        [Parameter(Mandatory)][ValidateSet('None','API','S3Bucket')][string]$UploadBackupZIP = (Read-Host "Upload To third Location"),
        [string]$APIEndpoint = 0,
        [string]$APIKey = 0
    )
    
    if($UseNetworkShare -eq "0"){
        if([string]::IsNullOrEmpty($BackupDest)){
            $BackupDest = Read-Host "Backup Path (Example: \\192.168.1.10\backup\)"
        }
        if([string]::IsNullOrEmpty($Username)){
            $Username = Read-Host "Backup-Path Username (Domain/Hostname\Username)"
        }
        if ([string]::IsNullOrEmpty($Password)) {
            $Password = Read-Host -AsSecureString "Backup-User Password"
        } elseif ($Password -isnot [System.Security.SecureString]) {
            $Password = ConvertTo-SecureString -String $Password -AsPlainText -Force
        }
        $DriveName = Get-DriveName
        if($BackupDest[$BackupDest.Length - 1] -eq "\"){
            $BackupDest = $BackupDest.Substring(0, $BackupDest.length - 1)
        }
        New-MapSMBShare -NetworkPath $BackupDest -DriveName $DriveName -Username $Username -Password $Password
    
        $yearpath = ($BackupDest + "\" + (Get-Date -Format "yyyy"))
        if(!(Test-Path -Path $yearpath)){
            New-Item -Path $yearpath -ItemType Directory
        }

        $KW = Get-CurrentWeekNumber
        $kwpath = $yearpath + "\" + $KW
        if(!(Test-Path -Path $kwpath)){
            New-Item -Path $kwpath -ItemType Directory
        }

        $fullpath = $kwpath + "\" + $env:COMPUTERNAME
        if(!(Test-Path -Path $fullpath)){
            New-Item -Path $fullpath -ItemType Directory
        }
    }else{
        if([string]::IsNullOrEmpty($BackupDest)){
            $mappedDrives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name.Length -eq 1 }
            # Create a numbered selection menu
            Write-Host "Select a drive:"
            for ($i = 0; $i -lt $mappedDrives.Count; $i++) {
                Write-Host "$($i+1): $($mappedDrives[$i].Name): ($($mappedDrives[$i].Root))"
            }

            # Prompt the user for selection
            $selection = Read-Host "Enter the number of the drive you want to use"

            # Validate input and get the selected drive
            if ($selection -match '^\d+$' -and [int]$selection -ge 1 -and [int]$selection -le $mappedDrives.Count) {
                $selectedDrive = $mappedDrives[[int]$selection - 1].Name
            } else {
                Write-Host "Invalid selection."
                break
            }
            $fullpath = $selectedDrive + ":"
        }else{
            if($BackupDest -match '^[A-Za-z]$'){
                $fullpath = $BackupDest + ":"
            }elseif($BackupDest -match '^[A-Za-z]:$'){
                $fullpath = $BackupDest
            }else{
                Write-Host "Invalid selection."
                break
            }
        }
    }

    wbadmin start backup -backupTarget:$fullpath -include:C: -allCritical -quiet
    
    if($UploadBackupZIP -ne 'None'){
        $backupzipfile = New-BackupZIP -fullpath $fullpath
    }

    switch($UploadBackupZIP){
        'None'{
            continue
        }
        'API'{
            if ($APIEndpoint -eq $null){
                $APIEndpoint = Read-Host "API Endpoint URL"
            }
            if ($APIKey -eq $null){
                $APIKey = Read-Host "API KEY"
            }
            Send-BackupToAPI -ZipFilePath $backupzipfile
        }
        'S3Bucket'{
            continue
        }
    }

    if($backupzipfile -ne $null){
        Remove-Item $backupzipfile -Force -Confirm:$false
    }
    
    Remove-MapSMBShare -DriveName $DriveName

}

New-Backup