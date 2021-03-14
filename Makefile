ADDONS_PATH=addons
INTERPRETER=python

ifeq ($(OS),Windows NT)
	INTERPRETER += .exe
endif

test:
	echo ${INTERPRETER}

## build-xml: Create addons.xml repo file
build-xml:
	${INTERPRETER} scripts/xml_generator.py -a ${ADDONS_PATH} -x ${ADDONS_PATH}/addons.xml

## build-zip: Create zip files when source version was changed
build-zip:
	${INTERPRETER} scripts/release.py -d ${ADDONS_PATH} -z ${ADDONS_PATH}/zip --md5

## build-zip-spec: Create single zip file or overwrite without md5
build-zip-spec:
	${INTERPRETER} scripts/release.py -f $(ADDON) -z ${ADDONS_PATH}/zip --force

## update-readme: Update README.md
update-readme:
	${INTERPRETER} scripts/readme_updater.py -d ${ADDONS_PATH} -z ${ADDONS_PATH}/zip -m README.md

release: build-xml build-zip

## help: Show this message and exit
help: Makefile
	@echo
	@echo " Choose a command run in kodi addons repo:"
	@echo
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo
