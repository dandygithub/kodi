# Dandy's KODI Addons Project

## Download zip repo file
[18 Lea](https://github.com/dandygithub/kodi/blob/master/addons/zip/repository.dandy.kodi/repository.dandy.kodi-1.4.2.zip?raw=true)  
[19 Matrix](https://github.com/dandygithub/kodi/blob/matrix/addons/zip/repository.dandy.kodi/repository.dandy.kodi-2.0.0.zip?raw=true)

## View source code
[18 Lea](https://github.com/dandygithub/kodi/tree/master)  
[19 Matrix](https://github.com/dandygithub/kodi/tree/matrix)

## Contribute
### Install
- [Python](https://www.python.org/downloads/)
- Make
### Steps
 1. **Fork** this repo on GitHub
 2. **Clone** the project to your own machine
 3. **Commit** changes to your own branch (*)
 4. **Push** your work back up to your fork
 5. Submit a **Pull request** so that we can review your changes

## Makefile commands (**)
- `make build-xml` Create addons.xml repo file
- `make build-zip` Create zip files when source version was changed
- `make build-zip-spec` Create single zip file or overwrite without md5
- `make update-readme` Update README.md
- `make release` build-xml + build-zip + update-readme

---
(*) _for the **GitHub Actions** work correctly, recommended to change the version in **plugin.xml**_ \
(**) _for **Matrix** branch only (optional, use **GitHub Actions** now)_
