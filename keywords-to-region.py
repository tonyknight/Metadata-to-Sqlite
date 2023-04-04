import os
import sys
import json
import sqlite3
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QMessageBox, QPushButton, QProgressBar
from PyQt5.QtCore import Qt
from tqdm import tqdm

class PhotoMetadataDatabase(QMainWindow):
    def __init__(self):
        super().__init__()

        # set up the main window
        self.setWindowTitle("Photo Metadata Database")
        self.setGeometry(100, 100, 1024, 1024)

        # add the folder label to the top of the window
        self.folder_label = QLabel(self)
        self.folder_label.setGeometry(50, 50, self.width() - 100, 50)
        self.folder_label.setAlignment(Qt.AlignCenter)

        # add the "Open Folder" button to the footer
        open_folder_button = QPushButton("Open Folder", self)
        open_folder_button.resize(200, 50)
        open_folder_button.move(int((self.width() - open_folder_button.width()) / 2),
                                int(self.height() - open_folder_button.height() - 50))
        open_folder_button.clicked.connect(self.select_folder)

        # add the "Create Database" button to the footer
        self.create_db_button = QPushButton("Create Database", self)
        self.create_db_button.setEnabled(False)
        self.create_db_button.resize(200, 50)
        self.create_db_button.move(int((self.width() - self.create_db_button.width()) / 2),
                                   int(open_folder_button.y() - self.create_db_button.height() - 20))
        self.create_db_button.clicked.connect(self.start_database_creation)


        # add the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, self.folder_label.height() + 100, self.width() - 100, 50)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # set up the photo folder variable
        self.photo_folder = None

    def select_folder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", options=options)
        if folder:
            self.photo_folder = folder
            self.folder_label.setText(self.photo_folder)
            self.create_db_button.setEnabled(True)

    def start_database_creation(self):
        # get the metadata for all photos in the folder
        cmd = self._get_exiftool_command()
        metadata_json = self._run_exiftool_command(cmd)
        if not metadata_json:
            return

        metadata = self._convert_metadata_json_to_list(metadata_json)

        # create the metadata table in the database
        conn = sqlite3.connect(os.path.join(self.photo_folder, "photo_metadata.db"))
        c = conn.cursor()
        self._create_metadata_table(c)
        conn.commit()
        conn.close()

        # dump metadata to a JSON file
        with open(os.path.join(self.photo_folder, "metadata.json"), "w") as f:
            json.dump(metadata, f)

        # insert the metadata into the database
        self._insert_metadata_into_database(metadata)

    def _run_exiftool_command(self, cmd):
        try:
            metadata_json_bytes = subprocess.check_output(cmd)
            metadata_json_str = metadata_json_bytes.decode("utf-8")
            metadata_json = json.loads(metadata_json_str)
            with open(os.path.join(self.photo_folder, "metadata.json"), "w") as f:
                json.dump(metadata_json, f)
            return metadata_json
        except subprocess.CalledProcessError as e:
            error_message = f"Error running Exiftool command: {e}"
            with open("errors.txt", "a") as f:
                f.write(error_message + "\n")
            QMessageBox.critical(self, "Error", error_message)
            return None

    def _convert_metadata_json_to_list(self, metadata_json):
        try:
            metadata_list = []
            for metadata_obj in metadata_json:
                metadata = {
                    "SourceFile": metadata_obj.get("SourceFile"),
                    "exif_DateTimeOriginal": metadata_obj.get("DateTimeOriginal"),
                    "exif_ModifyDate": metadata_obj.get("ModifyDate"),
                    "exif_Model": metadata_obj.get("Model"),
                    "exif_CameraModelName": metadata_obj.get("CameraModelName"),
                    "exif_ISO": metadata_obj.get("ISO"),
                    "exif_Notes": metadata_obj.get("Notes"),
                    "exif_ImageDescription": metadata_obj.get("ImageDescription"),
                    "exif_UserComment": metadata_obj.get("UserComment"),
                    "exif_GPSLongitude": metadata_obj.get("GPSLongitude"),
                    "exif_GPSLatitude": metadata_obj.get("GPSLatitude"),
                    "iptc_Sub_Location": metadata_obj.get("IPTC:Sub-location"),
                    "iptc_City": metadata_obj.get("IPTC:City"),
                    "iptc_Province_State": metadata_obj.get("IPTC:Province-State"),
                    "iptc_Country_PrimaryLocationName": metadata_obj.get("IPTC:Country-PrimaryLocationName"),
                    "iptc_Category": metadata_obj.get("IPTC:Category"),
                    "iptc_Headline": metadata_obj.get("IPTC:Headline"),
                    "iptc_Caption": metadata_obj.get("IPTC:Caption"),
                    "iptc_Source": metadata_obj.get("IPTC:Source"),
                    "iptc_Caption_Abstract": metadata_obj.get("IPTC:Caption-Abstract"),
                    "iptc_Notes": metadata_obj.get("IPTC:Notes"),
                    "iptc_FixtureIdentifier": metadata_obj.get("IPTC:FixtureIdentifier"),
                    "iptc_Contact": metadata_obj.get("IPTC:Contact"),
                    "iptc_Keywords": metadata_obj.get("IPTC:Keywords"),
                    "xmp_Event": metadata_obj.get("XMP:Event"),
                    "xmp_Location": metadata_obj.get("XMP:Location"),
                    "xmp_Sub_Location": metadata_obj.get("XMP:Sub-location"),
                    "xmp_City": metadata_obj.get("XMP:City"),
                    "xmp_Province_State": metadata_obj.get("XMP:Province-State"),
                    "xmp_Country_PrimaryLocationName": metadata_obj.get("XMP:Country-PrimaryLocationName"),
                    "xmp_Description": metadata_obj.get("XMP:Description"),
                    "xmp_UserComment": metadata_obj.get("XMP:UserComment"),
                    "xmp_Keywords": metadata_obj.get("XMP:Keywords"),
                    "xmp_People": metadata_obj.get("XMP:People"),
                    "xmp_PersonInImage": metadata_obj.get("XMP:PersonInImage"),
                    "xmp_TagsList": metadata_obj.get("XMP:TagsList"),
                    "xmp_CatalogSets": metadata_obj.get("XMP:CatalogSets"),
                    "xmp_HierarchicalSubject": metadata_obj.get("XMP:HierarchicalSubject")
                }
                metadata_list.append(metadata)
                # print out the values of the metadata dictionary for debugging
                print(metadata)
            return metadata_list
        except json.JSONDecodeError as e:
            error_message = f"Error decoding JSON: {e}"
            with open("errors.txt", "a") as f:
                f.write(error_message + "\n")
            QMessageBox.critical(self, "Error", error_message)
            return []

    def _create_metadata_table(self, cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_metadata (
                SourceFile TEXT,
                exif_DateTimeOriginal TEXT, 
                exif_ModifyDate TEXT, 
                exif_Model TEXT, 
                exif_CameraModelName TEXT, 
                exif_ISO TEXT, 
                exif_Notes TEXT, 
                exif_ImageDescription TEXT, 
                exif_UserComment TEXT, 
                exif_GPSLongitude TEXT, 
                exif_GPSLatitude TEXT, 
                iptc_Sub_Location TEXT, 
                iptc_City TEXT, 
                iptc_Province_State TEXT, 
                iptc_Country_PrimaryLocationName TEXT, 
                iptc_Category TEXT, 
                iptc_Headline TEXT, 
                iptc_Caption TEXT, 
                iptc_Source TEXT, 
                iptc_Caption_Abstract TEXT, 
                iptc_Notes TEXT, 
                iptc_FixtureIdentifier TEXT, 
                iptc_Contact TEXT, 
                iptc_Keywords TEXT, 
                xmp_Event TEXT, 
                xmp_Location TEXT, 
                xmp_Sub_Location TEXT, 
                xmp_City TEXT, 
                xmp_Province_State TEXT, 
                xmp_Country_PrimaryLocationName TEXT, 
                xmp_Description TEXT, 
                xmp_UserComment TEXT, 
                xmp_Keywords TEXT, 
                xmp_People TEXT, 
                xmp_PersonInImage TEXT, 
                xmp_TagsList TEXT, 
                xmp_CatalogSets TEXT, 
                xmp_HierarchicalSubject TEXT
            )
        """)

    def _insert_metadata_into_database(self, metadata):
        # Column map
        column_map = {
            "SourceFile": "SourceFile",
            "DateTimeOriginal": "exif_DateTimeOriginal",
            "ModifyDate": "exif_ModifyDate",
            "Model": "exif_Model",
            "CameraModelName": "exif_CameraModelName",
            "ISO": "exif_ISO",
            "Notes": "exif_Notes",
            "ImageDescription": "exif_ImageDescription",
            "UserComment": "exif_UserComment",
            "GPSLongitude": "exif_GPSLongitude",
            "GPSLatitude": "exif_GPSLatitude",
            "IPTC:Sub-location": "iptc_Sub_Location",
            "IPTC:City": "iptc_City",
            "IPTC:Province-State": "iptc_Province_State",
            "IPTC:Country-PrimaryLocationName": "iptc_Country_PrimaryLocationName",
            "IPTC:Category": "iptc_Category",
            "IPTC:Headline": "iptc_Headline",
            "IPTC:Caption": "iptc_Caption",
            "IPTC:Source": "iptc_Source",
            "IPTC:Caption-Abstract": "iptc_Caption_Abstract",
            "IPTC:Notes": "iptc_Notes",
            "IPTC:FixtureIdentifier": "iptc_FixtureIdentifier",
            "IPTC:Contact": "iptc_Contact",
            "IPTC:Keywords": "iptc_Keywords",
            "XMP:Event": "xmp_Event",
            "XMP:Location": "xmp_Location",
            "XMP:Sub-location": "xmp_Sub_Location",
            "XMP:City": "xmp_City",
            "XMP:Province-State": "xmp_Province_State",
            "XMP:Country-PrimaryLocationName": "xmp_Country_PrimaryLocationName",
            "XMP:Description": "xmp_Description",
            "XMP:UserComment": "xmp_UserComment",
            "XMP:Keywords": "xmp_Keywords",
            "XMP:People": "xmp_People",
            "XMP:PersonInImage": "xmp_PersonInImage",
            "XMP:TagsList": "xmp_TagsList",
            "XMP:CatalogSets": "xmp_CatalogSets",
            "XMP:HierarchicalSubject": "xmp_HierarchicalSubject"
        }

        # Inserts the photo metadata into the SQLite database.
        conn = sqlite3.connect(os.path.join(self.photo_folder, "photo_metadata.db"))
        c = conn.cursor()

        # loop through the metadata and insert it into the SQLite database
        self.progress_bar.setMaximum(len(metadata))
        for i, photo_metadata in enumerate(tqdm(metadata)):
            # get the values from the photo_metadata dictionary
            values = [photo_metadata.get(column_map[key]) for key in column_map]
            # insert the metadata into the SQLite database
            c.execute(
                f"INSERT INTO photo_metadata ({','.join(column_map.values())}) VALUES ({','.join(['?'] * len(column_map))})",
                values)

            self.progress_bar.setValue(i + 1)

        # commit the changes and close the connection
        conn.commit()
        conn.close()

    def _get_exiftool_command(self):
        # Define the list of metadata tags to extract
        metadata_tags = [
            '-exif:DateTimeOriginal',
            '-exif:ModifyDate',
            '-exif:Model',
            '-exif:CameraModelName',
            '-exif:ISO',
            '-exif:Notes',
            '-exif:ImageDescription',
            '-exif:UserComment',
            '-exif:GPSLongitude',
            '-exif:GPSLatitude',
            '-iptc:Sub-location',
            '-iptc:City',
            '-iptc:Province-State',
            '-iptc:Country-PrimaryLocationName',
            '-iptc:Category',
            '-iptc:Headline',
            '-iptc:Caption',
            '-iptc:Source',
            '-iptc:Caption-Abstract',
            '-iptc:Notes',
            '-iptc:FixtureIdentifier',
            '-iptc:Contact',
            '-iptc:Keywords',
            '-xmp:Event',
            '-xmp:Location',
            '-xmp:Sub-location',
            '-xmp:City',
            '-xmp:Province-State',
            '-xmp:Country-PrimaryLocationName',
            '-xmp:Description',
            '-xmp:UserComment',
            '-xmp:Keywords',
            '-xmp:People',
            '-xmp:PersonInImage',
            '-xmp:TagsList',
            '-xmp:CatalogSets',
            '-xmp:HierarchicalSubject',
        ]

        # add the metadata tags to the Exiftool command
        return ['exiftool', '-j'] + metadata_tags + [self.photo_folder]

if __name__ == '__main__':
        app = QApplication(sys.argv)
        window = PhotoMetadataDatabase()
        window.show()
        sys.exit(app.exec_())


