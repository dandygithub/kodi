ADDONS_PATH=addons
INTERPRETER=python3
WHERE=which

ifeq ($(OS),Windows_NT)
        INTERPRETER=python
	WHERE=where
endif

test:
	@${WHERE} ${INTERPRETER}
	@${INTERPRETER} --version
	

## build-xml: Create addons.xml repo file
build-xml:
	@echo ----------------------------
	@echo Create addons.xml repo file
	@echo ----------------------------        
	@${INTERPRETER} scripts/xml_generator.py -a ${ADDONS_PATH} -x ${ADDONS_PATH}/addons.xml

## build-zip: Create zip files when source version was changed
build-zip:
	@echo -------------------------------------------------
	@echo Create zip files when source version was changed
	@echo -------------------------------------------------        
	@${INTERPRETER} scripts/release.py -d ${ADDONS_PATH} -z ${ADDONS_PATH}/zip --md5

## build-zip-spec: Create single zip file or overwrite without md5
build-zip-spec:
	@echo ------------------------------------------------
	@echo Create single zip file or overwrite without md5
	@echo ------------------------------------------------        
	@${INTERPRETER} scripts/release.py -f $(ADDON) -z ${ADDONS_PATH}/zip --force

## update-readme: Update README.md
update-readme:
	@echo -----------------
	@echo Update README.md
	@echo -----------------        
	@${INTERPRETER} scripts/readme_updater.py -d ${ADDONS_PATH} -z ${ADDONS_PATH}/zip -m README.md

## release: build-xml + build-zip + update-readme
release: build-xml build-zip update-readme

## help: Show this message and exit
ifneq ($(OS),Windows_NT)
help: Makefile
	@echo
	@echo " Choose a command run in kodi addons repo:"
	@echo
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo
endif		
