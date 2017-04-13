import os
import xml.etree.ElementTree as XML
import md5

def _save_file(data, file):
    try:
        # write data to the file
        open(file, "w").write(data)
    except Exception, e:
        # oops
        print "An error occurred saving %s file!\n%s" % ( file, e, )

def _generate_md5_file(archive):
    try:
        # create a new md5 hash
        m = md5.new(open(archive).read()).hexdigest()
        # save file
        _save_file(m, file = archive + ".md5")
    except Exception, e:
        # oops
        print "An error occurred creating " + archive + " md5 file!\n%s" % ( e, )

for directory in os.listdir("."):
    if not directory.startswith('.'):
        if 'plugin' in directory or 'script' in directory or 'repository' in directory or 'skin' in directory or 'context' in directory:
            # Create plugin directory if not exist
            zip_dir = os.path.join(os.getcwd(), 'zip', directory)
            fulldir = os.path.join(os.getcwd(), directory)
            if not os.path.exists(zip_dir):
                os.makedirs(zip_dir)

            os.system("copy /Y %s %s" %(os.path.join(fulldir, "icon.png"), zip_dir))
            os.system("copy /Y %s %s" %(os.path.join(fulldir, "fanart.jpg"), zip_dir))
            os.system("copy /Y %s %s" %(os.path.join(fulldir, "changelog.txt"), zip_dir))

            # Get plugin name and version from addon.xml
            addon = XML.parse('%s/addon.xml' % directory).getroot()
            name = '%s-%s.zip' %(addon.attrib['id'], addon.attrib['version'])
            archive = os.path.join(os.getcwd(), 'zip', zip_dir, name)

            if not os.path.isfile(archive):
                print "Release new version of %s" % name
                print "Create ZIP archive %s" % archive
                os.system("7z a %s %s" %(archive, directory))
                if os.path.isfile(archive):
                    _generate_md5_file(archive)    
