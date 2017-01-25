import os
import xml.etree.ElementTree as XML

for directory in os.listdir("."):
    if not directory.startswith('.'):
        if 'plugin' in directory or 'script' in directory or 'repository' in directory or 'skin' in directory:
            # Create plugin directory if not exist
            zip_dir = os.path.join(os.getcwd(), 'zip', directory)
            if not os.path.exists(zip_dir):
                os.makedirs(zip_dir)

            # Get plugin name and version from addon.xml
            addon = XML.parse('%s/addon.xml' % directory).getroot()
            name = '%s-%s.zip' %(addon.attrib['id'], addon.attrib['version'])
            archive = os.path.join(os.getcwd(), 'zip', zip_dir, name)

            if not os.path.isfile(archive):
                print "Release new version of %s" % name
                print "Create ZIP archive %s" % archive
                os.system("zip -r %s %s" %(archive, directory))
