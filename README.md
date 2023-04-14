# Metadata-to-Sqlite
Creates a sqlite database using metadata extracted from photos using exiftool.

## Usage
1. Start with editing the tags.json file. This contains exiftool tag groups and tag names followed by the sqlite column names. Add or subtract tags as needed. The exiftool command and sqlite column names are generated based on this file.
2. Either load a directory of photos (which will be index recursively) or load a pre-existing exiftool produced json file. The Create Database button should be able to understand your choice and either create json file or use the existing json file to create the sqlite database.

Enjoy!

## To Fix..
- State and Country names not being passed to db, but appear in the metadata.json file. Could be a hyphen issue.
- Check to make sure all the Region tags are in db.

## Data Clean up
To make sure the database is as clean as possible, use these exiftools commands to sanitize the data:

- Clear region fields if no region rectangle is in the photo metadata:
```exiftool -if 'not $RegionRectangle' -RegionPersonDisplayName= -RegionType= -RegionName= -ext jpg -ext png -ext tiff -overwrite_original dir/```
- Remove leftover 'People' tag from RegionPersonDisplayName
```exiftool -if '$RegionPersonDisplayName eq "People"' -RegionPersonDisplayName= -ext jpg -ext png -ext tiff -overwrite_original dir/```
