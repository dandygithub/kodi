""" addons.xml generator """
import os
import logging
from hashlib import md5
import argparse

logging.basicConfig(
    level=logging.INFO
)


def generate_addons_xml(path, exclude_paths):
    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    for file_name in os.listdir(path):
        full_path = os.path.join(path, file_name)
        if not os.path.isdir(full_path) or file_name in exclude_paths:
            continue
        addon_xml_file = os.path.join(full_path, 'addon.xml')
        if not os.path.exists(addon_xml_file):
            logging.warning('file: %s not exist, continue', addon_xml_file)
            continue
        with open(addon_xml_file, 'r') as file:
            addon_xml = ''
            for line in file.readlines():
                if line.find('<?xml') >= 0:
                    continue
                addon_xml += line
            addons_xml += addon_xml.rstrip() + "\n\n"
    return addons_xml.strip() + "\n</addons>\n"


def generate_md5(file_path):
    with open(file_path, 'rb') as file:
        digest = md5(file.read()).hexdigest()
        save_file(file_path + '.md5', digest)


def save_file(file_path, data):
    with open(file_path, 'w') as file:
        file.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-a', dest='addons_path', type=str, default='addons', help='addons src path')
    parser.add_argument('-x', dest='xml_file', type=str, default='addon.xml', help='result xml file')
    parser.add_argument('-e', dest='exclude_paths', type=list, default=['zip', 'DEPRECATED'], help='ignored paths')
    args = parser.parse_args()

    xml_body = generate_addons_xml(os.path.join(os.getcwd(), args.addons_path), args.exclude_paths)
    save_file(args.xml_file, xml_body)
    logging.info('%s created success', args.xml_file)
    generate_md5(args.xml_file)
    logging.info('md5 file for %s created success', args.xml_file)
