ADDONS_PATH=addons

build-xml:
	python scripts/xml_generator.py -a ${ADDONS_PATH} -x ${ADDONS_PATH}/addons.xml

build-zip:
	python scripts/release.py -a ${ADDONS_PATH} -z ${ADDONS_PATH}/zip
