import os
import argparse
from release import search_addons, get_addon_attributes

HEADER = "# Dandy's KODI Addons Project"


def get_addons_info(addons_path):
    mapper = {}
    for addon_path in search_addons(addons_path):
        _id, name, version = get_addon_attributes(addon_path)
        mapper[_id] = {
            'name': name,
            'version': version,
        }
    return mapper


def read_file(path):
    with open(path, 'r') as file:
        return file.read()


def generate(addons_mapper, zip_path):
    lines = [
        HEADER,
        "### Addons",
        "|icon|name|id|latest|md5sum|",
        "|---|---|---|---|---|"
    ]
    for folder_name, sub_folders, filenames in os.walk(zip_path):
        addon_id = os.path.basename(folder_name)
        addon_properties = addons_mapper.get(addon_id)
        if not addon_properties:
            continue

        addon = {
            'name': addon_properties['name'],
            'id': addon_id,
        }
        icon_path = os.path.join(folder_name, 'icon.png')
        if os.path.exists(icon_path):
            addon['icon'] = icon_path + '?raw=true'

        releases = []
        for filename in filenames:
            if filename.endswith('.zip'):
                releases.append(os.path.join(folder_name, filename))
        if not releases:
            continue
        releases.sort(reverse=True)
        for release in releases:
            md5_file = release + '.md5'
            if os.path.exists(md5_file):
                addon['r_zip'] = release + '?raw=true'
                addon['r_name'] = release.split('-')[-1]
                addon['r_md5'] = read_file(md5_file)
                break

        lines.append(
            f"|![]({addon['icon']})|{addon['name']}|{addon['id']}|[{addon['r_name']}]({addon['r_zip']})|`{addon['r_md5']}`|"
        )
    return lines


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-d', dest='addons_path', type=str, help='addons source path')
    parser.add_argument('-z', dest='zip_path', type=str, default='addons/zip', help='zip dst path')
    parser.add_argument('-m', dest='md_file', type=str, help='md file')
    args = parser.parse_args()

    storage = get_addons_info(args.addons_path)
    with open(args.md_file, 'w') as file:
        for line in generate(storage, args.zip_path):
            file.write(line + '\n')
