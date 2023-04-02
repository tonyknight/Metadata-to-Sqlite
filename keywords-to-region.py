import subprocess
import sqlite3
import json
import os

# define the path to your photo folder
photo_folder = "/path/to/your/photo/folder"

# define the Exiftool command to extract all metadata tags
exiftool_cmd = ['exiftool', '-j', '-iptc:all', '-exif:all', '-xmp:all', photo_folder]

# call the Exiftool command using the subprocess module
metadata_json = subprocess.check_output(exiftool_cmd)

# convert the JSON string to a Python list of dictionaries
metadata = json.loads(metadata_json)

# create a SQLite database and a table to store the metadata
db_path = os.path.join(photo_folder, "photo_metadata.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# retrieve a list of all the tag names present in the photos
tag_names = set()
for photo_metadata in metadata:
    iptc = photo_metadata.get('IPTC', {})
    exif = photo_metadata.get('EXIF', {})
    xmp = photo_metadata.get('XMP', {})
    tag_names.update(iptc.keys())
    tag_names.update(exif.keys())
    tag_names.update(xmp.keys())

# create a table with columns for each tag name
c.execute('CREATE TABLE IF NOT EXISTS photo_metadata ({})'.format(', '.join(['{} text'.format(tag_name) for tag_name in tag_names])))

# loop through the metadata and insert it into the SQLite database
for photo_metadata in metadata:
    row = {tag_name: photo_metadata.get('IPTC', {}).get(tag_name, None) for tag_name in tag_names}
    row.update({tag_name: photo_metadata.get('EXIF', {}).get(tag_name, None) for tag_name in tag_names})
    row.update({tag_name: photo_metadata.get('XMP', {}).get(tag_name, None) for tag_name in tag_names})
    c.execute("INSERT INTO photo_metadata ({}) VALUES ({})".format(', '.join(row.keys()), ', '.join(['?' for _ in row.values()])), tuple(row.values()))

# commit the changes and close the connection
conn.commit()
conn.close()
