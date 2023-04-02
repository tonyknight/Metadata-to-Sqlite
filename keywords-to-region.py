import subprocess
import sqlite3
import json
import os

# define the path to your photo folder
photo_folder = "/path/to/your/photo/folder"

# define the Exiftool command to extract metadata
exiftool_cmd = ['exiftool', '-j', '-iptc:all', '-exif:all', '-xmp:all', photo_folder]

# call the Exiftool command using the subprocess module
metadata_json = subprocess.check_output(exiftool_cmd)

# convert the JSON string to a Python list of dictionaries
metadata = json.loads(metadata_json)

# create a SQLite database and a table to store the metadata
db_path = os.path.join(photo_folder, "photo_metadata.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS photo_metadata
             (filename text, iptc text, exif text, xmp text)''')

# loop through the metadata and insert it into the SQLite database
for photo_metadata in metadata:
    filename = photo_metadata.get('SourceFile', '')
    iptc = json.dumps(photo_metadata.get('IPTC', {}))
    exif = json.dumps(photo_metadata.get('EXIF', {}))
    xmp = json.dumps(photo_metadata.get('XMP', {}))
    c.execute("INSERT INTO photo_metadata VALUES (?, ?, ?, ?)", (filename, iptc, exif, xmp))

# commit the changes and close the connection
conn.commit()
conn.close()
