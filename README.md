# Keywords-to-Regions
Creates a sqlite database using metadata extracted from photos using exiftool.

## To Fix..
- State and Country names not being passed to db, but appear in the the metadata.json file. Could be a hypen issue.
- Check to make sure all the Region tags are in db.

## Data Clean up
To make sure the database is as clean as possible, use these exiftools commands to sanitiset the data:

- Clear region fields if no region rectangle is in the photo metadata:
```exiftool -if 'not $RegionRectangle' -RegionPersonDisplayName= -RegionType= -RegionName= -ext jpg -ext png -ext tiff -overwrite_original dir/```
- Remove leftover 'People' tag from RegionPersonDisplayName
```exiftool -if '$RegionPersonDisplayName eq "People"' -RegionPersonDisplayName= -ext jpg -ext png -ext tiff -overwrite_original dir/```
