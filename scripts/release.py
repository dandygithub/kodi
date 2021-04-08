import os
import argparse
from shutil import copy2
from xml.etree import ElementTree
from zipfile import ZipFile
import logging

from xml_generator import generate_md5

logging.basicConfig(
    level=logging.INFO
)

AVAILABLE_PREFIX = [
    'plugin',
    'script',
    'repository',
    'skin',
    'context',
]


def search_addons(path):
    targets = []
    for file_name in os.listdir(path):
        full_path = os.path.join(path, file_name)
        if not os.path.isdir(full_path):
            logging.debug('%s is not directory, continue', full_path)
            continue
        for prefix in AVAILABLE_PREFIX:
            if file_name.startswith(prefix + '.'):
                logging.debug('found new target addon: %s', full_path)
                targets.append(full_path)
    return targets


def get_addon_attributes(src_path):
    addon = ElementTree.parse(os.path.join(src_path, 'addon.xml')).getroot()
    description = ''
    for extension in addon.iter('extension'):
        item = extension.find('summary')
        if item != None:
            description = item.text
    return addon.attrib["id"], addon.attrib["name"], addon.attrib["version"], description


def prepare_release_folder(src_addon, dst_path):
    if not os.path.exists(dst_path):
        logging.info('create new directory %s', dst_path)
        os.makedirs(dst_path)
    for static_file in ['icon.png', 'fanart.jpg', 'changelog.txt']:
        src_file = os.path.join(src_addon, static_file)
        try:
            copy2(src_file, dst_path)
        except FileNotFoundError:
            logging.debug('src file: %s does not exist, continue', src_file)
            continue


def compress_zip(src_path, dst_file):
    root = os.path.basename(src_path)
    with ZipFile(dst_file, 'w') as file:
        for folder_name, sub_folders, filenames in os.walk(src_path):
            for filename in filenames:
                full_path = os.path.join(folder_name, filename)
                file.write(full_path, os.path.join(root, str(full_path.split(root)[-1])[1:]))
    return dst_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-d', dest='addons_path', type=str, help='addons source path')
    parser.add_argument('-f', dest='addon', type=str, help='single addon source path')
    parser.add_argument('-z', dest='zip_path', type=str, default='addons/zip', help='zip dst path')
    parser.add_argument('--md5', dest='md5', action='store_true', help='create md5 file')
    parser.add_argument('--force', dest='force', action='store_true', help='force create zip file (overwrite)')
    args = parser.parse_args()

    target_addons = []
    if args.addons_path:
        for plugin in search_addons(args.addons_path):
            target_addons.append(plugin)
    else:
        target_addons.append(args.addon)

    for target in target_addons:
        addon_id, addon_name, addon_version, addon_description = get_addon_attributes(target)
        release_path = os.path.join(args.zip_path, addon_id)
        prepare_release_folder(target, release_path)
        addon_zip_path = os.path.join(release_path, '{}-{}.zip'.format(addon_id, addon_version))
        if not args.force and os.path.exists(addon_zip_path):
            logging.debug('zip file: %s exist, continue', addon_zip_path)
            continue
        logging.info('release new addon name: %s id: %s version: %s', addon_name, addon_id, addon_version)
        if target.endswith('/'):
            target = target[:-1]
        logging.info('create ZIP archive: %s', addon_zip_path)
        compress_zip(target, addon_zip_path)
        if args.md5:
            logging.info('generate md5 file: %s', addon_zip_path)
            generate_md5(addon_zip_path)
