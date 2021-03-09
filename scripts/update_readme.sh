echo "# Dandy's KODI Addons Project"

echo "|icon|plugin|zip|md5|"
echo "|---|---|---|---|"
for PLUGIN in $(ls $1)
do
  ZIP_FILE=$(ls $1$PLUGIN/*.zip | sort | tail -1)
  ICON=$(echo $1$PLUGIN/icon.png?raw=true)
  VERSION=$(echo $ZIP_FILE | rev | cut -d "-" -f 1 | rev)
  MD5=$(cat $ZIP_FILE.md5)
  echo "|![icon]($ICON)|$PLUGIN|[$VERSION]($ZIP_FILE?raw=true)|\`$MD5\`|"
done