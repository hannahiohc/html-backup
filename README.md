# HTML Backup

HTML Backup creates a timestamped backup of `index.html` files in the folders you specify.<br />
This is useful for comparing old and new code, especially when code changes are made daily.<br />
Run this tool before running `svn update`.<br />
It can also delete old backup files, or check if your `index.html` files have updates available in SVN.

## Setup
**1. Save `html-backup.py`**
```
/path/to/...
```
<br />

**2. Edit the `PATH_SETS` list with the folders you want to back up**
> Each folder listed must contain an `index.html` file.
```
PATH_SETS = {
    "branch-01": [
        "/phone",
        "/phone/specs",
        "/phone/compare",
    ],
    "branch-02": [
        "/watch",
        "/watch/compare",
        "/watch/feature-availity",
    ],
    "branch-03": [
        "/os",
        "/os/ios",
        "/os/macos",
        "/os/watchos",
    ],
}
```
<br />

**3. Make the script executable**
```
chmod +x /path/to/html-backup.py
```
<br />

**4. Add a shortcut to your path**
```
ln -s /path/to/html-backup.py /usr/local/bin/html-backup
```

## Usage
**1. Navigate to the branch you want to update**
```
cd us/branches/branch-01/us 
```
<br />

**2. Back up index.html files**
> The script will create backup files named `__index_YYMMDD-HHMM_r######.bak.html` in the same folders as the original `index.html`.
- Backup all sets
```
html-backup
```
- Backup a specific set
```
html-backup $path-set-name
```
<br />

**3. Delete backup files**
- Delete backups in all sets
```
html-backup delete
```
- Delete backups in a specific set
```
html-backup delete $path-set-name
```
<br />

**4. Check for SVN updates**
- Check all sets
```
html-backup check
```
- Check a specific set
```
html-backup check $path-set-name
```

## Help
Show usage and available sets
```
html-backup help
```
