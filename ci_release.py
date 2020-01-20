import os
from shutil import copyfile
import xml.etree.ElementTree as XML
from hashlib import md5

ADDONS_PATH = os.path.join(os.getcwd(), 'addons')

TARGETS = [
    'plugin',
    'script',
    'repository',
    'skin',
    'context'
]


def _save_file(data, file_name):
    try:
        with open(file_name, 'w') as file:
            file.write(data)
    except Exception as e:
        print(f"An error occurred saving %{file_name} file!\n{e}")


def _generate_md5(src_file):
    try:
        with open(src_file, 'rb') as file:
            m = md5(file.read()).hexdigest()
            _save_file(m, file_name=archive + ".md5")
    except Exception as e:
        print(f'An error occurred creating "{archive}" md5 file!\n{e}')


def copy_addition_files(src, dst):
    for addition in ['icon.png', 'fanart.jpg', 'changelog.txt']:
        try:
            copyfile(
                os.path.join(src, addition),
                os.path.join(dst, addition)
            )
        except FileNotFoundError:
            continue


if __name__ == '__main__':
    for directory in os.listdir(ADDONS_PATH):
        if directory.startswith('.'):
            continue
        if not any(map(lambda x: x in directory, TARGETS)):
            continue
        # Create plugin directory if not exist
        zip_dir = os.path.join(ADDONS_PATH, 'zip', directory)
        full_dir = os.path.join(ADDONS_PATH, directory)
        if not os.path.exists(zip_dir):
            os.makedirs(zip_dir)
        copy_addition_files(full_dir, zip_dir)
        # Get plugin name and version from addon.xml
        addon = XML.parse(
            os.path.join(ADDONS_PATH, directory, 'addon.xml')
        ).getroot()
        name = f"{addon.attrib['id']}-{addon.attrib['version']}.zip"
        archive = os.path.join(ADDONS_PATH, 'zip', zip_dir, name)
        if not os.path.isfile(archive):
            print(f"Release new version of: {name}")
            print(f"Create ZIP archive: {archive}")
            os.system("7z a %s %s" % (archive, directory))
            if os.path.isfile(archive):
                _generate_md5(archive)
