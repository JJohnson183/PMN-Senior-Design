# PMN Local Dev Site Setup

## Guides Followed

### Setting Up DDEV
 - https://ddev.com/get-started/

### Importing PMN site to local dev
 - https://dev.to/mandrasch/import-wordpress-site-into-local-project-via-ddev-backwpup-18p6

## Initial Setup


### 1) Install WSL
Run the following in PowerShell terminal:

```
wsl --install --no-distribution
```

If wsl is already installed, update it before proceeding.

```
wsl --update
```

Create the Ubuntu distro for ddev.

```
wsl --install Ubuntu-26.04 --name DDEV
```

Verify the installation

```
> wsl -l -v
NAME                   STATE           VERSION
* DDEV                   Stopped         2
```


### 2) Install DDEV
Install DDEV from the following link

```
Download Link
https://ddev.com/download/ddev_windows_amd64_installer.exe
```

Run the installer selecting the preferred "Docker CE" approach and selecting your "DDEV" distro.

In the “DDEV” terminal app or Windows Terminal "DDEV" profile, confirm that the ddev binary is installed: 🎉

```
> ddev --version
ddev version v1.25.5
```

### 3) Pulling in PMN Site Backup
Download the backup from the [PMN site](https://publicmedianet.org/wp-admin/admin.php?page=backwpupbackups&action=delete&jobdest-top=1_FOLDER&backupfiles%5B0%5D=%2Fhome%2Fwp_9hci6e%2Fpublicmedianet.org%2Fwp-content%2Fuploads%2Fbackwpup%2Fd72fbb%2Fbackups%2F2026-11-08_17-52-39_5LLS7O5202_FILE-DBDUMP-WPPLUGIN.zip&paged=1&_wpnonce=985b7f0a7f) using the BackWPup plugin.

Navigate to the `local_wp/` folder and save this backup as `backup.zip`

Run `ddev start` in the `local_wp/` folder

Run `ddev pull backup` to start the import. This will take a while.

You can now run `ddev launch` to open the site locally in your browser!


