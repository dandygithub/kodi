import os
from shutil import copy2
from xml.etree import ElementTree
from zipfile import ZipFile
import argparse
from xml_generator import generate_md5

AVAILABLE_PREFIX = [
    'plugin',
    'script',
    'repository',
    'skin',
    'context',
]


def get_target_plugins(path):
    targets = []
    for file_name in os.listdir(path):
        full_path = os.path.join(path, file_name)
        if not os.path.isdir(full_path):
            continue
        for prefix in AVAILABLE_PREFIX:
            if file_name.startswith(prefix + '.'):
                targets.append(full_path)
    return targets


def build_zip(src_plugin, zip_path):
    dst_zip = os.path.join(zip_path, os.path.basename(src_plugin))
    if not os.path.exists(zip_path):
        os.makedirs(zip_path)
    for static_file in ['icon.png', 'fanart.jpg', 'changelog.txt']:
        try:
            copy2(os.path.join(src_plugin, static_file), dst_zip)
        except FileNotFoundError:
            continue

    addon = ElementTree.parse(os.path.join(src_plugin, 'addon.xml')).getroot()
    archive = os.path.join(dst_zip, f'{addon.attrib["id"]}-{addon.attrib["version"]}.zip')
    if os.path.exists(archive):
        return
    print(f'release new addon: {addon.attrib["id"]} version: {addon.attrib["version"]}')
    print(f'create ZIP archive: {archive}')
    with ZipFile(archive, 'w') as file:
        for folder_name, sub_folders, filenames in os.walk(src_plugin):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                file.write(file_path, addon.attrib["id"] + str(file_path.split(addon.attrib["id"])[-1]))
    generate_md5(archive)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-a', dest='addons_path', type=str, default='addons', help='addons src path')
    parser.add_argument('-z', dest='zip_path', type=str, default='addons/zip', help='zip dst path')
    args = parser.parse_args()

    for plugin in get_target_plugins(args.addons_path):
        build_zip(plugin, os.path.join(os.getcwd(), args.zip_path))
