import os
import sys
import json
import sqlite3
import subprocess
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QPushButton, QProgressBar
from PyQt5.QtCore import Qt
from tqdm import tqdm


class PhotoMetadataDatabase(QMainWindow):
    def __init__(self):
        super().__init__()

        # set up the main window
        self.setWindowTitle("Photo Metadata Database")
        self.setGeometry(100, 100, 1024, 1024)

        # add the "Open Folder" button to the footer
        open_folder_button = QPushButton("Open Folder", self)
        open_folder_button.resize(200, 50)
        open_folder_button.move((self.width() - open_folder_button.width()) / 2, self.height() - open_folder_button.height() - 50)
        open_folder_button.clicked.connect(self.select_folder)

        # add the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 50, self.width() - 100, 50)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # set up the photo folder variable
        self.photo_folder = None


    def select_folder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", options=options)
        if folder:
            self.photo_folder = folder


    def create_database(self):
        # define the start time
        self.start_time = time.time()
        # define the Exiftool command to extract all metadata tags
        exiftool_cmd = ['exiftool', '-j', '-iptc:all', '-exif:all', '-xmp:all', self.photo_folder]

        # call the Exiftool command using the subprocess module
        metadata_json = subprocess.check_output(exiftool_cmd)

        # convert the JSON string to a Python list of dictionaries
        metadata = json.loads(metadata_json)

        # create a SQLite database and a table to store the metadata
        db_path = os.path.join(self.photo_folder, "photo_metadata.db")
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
        c.execute('CREATE TABLE IF NOT EXISTS photo_metadata ({})'.format(
            ', '.join(['{} text'.format(tag_name) for tag_name in tag_names])))

        # loop through the metadata and insert it into the SQLite database
        self.progress_bar.setMaximum(len(metadata))
        for i, photo_metadata in enumerate(tqdm(metadata)):
            row = {tag_name: photo_metadata.get('IPTC', {}).get(tag_name, None) for tag_name in tag_names}
            row.update({tag_name: photo_metadata.get('EXIF', {}).get(tag_name, None) for tag_name in tag_names})
            row.update({tag_name: photo_metadata.get('XMP', {}).get(tag_name, None) for tag_name in tag_names})
            c.execute("INSERT INTO photo_metadata ({}) VALUES ({})".format(', '.join(row.keys()),
                                                                           ', '.join(['?' for _ in row.values()])),
                      tuple(row.values()))
            self.progress_bar.setValue(i + 1)

        # commit the changes and close the connection
        conn.commit()
        conn.close()

        # show an alert box with the indexing results
        total_time = time.time() - self.start_time
        num_photos = len(metadata)
        message = "Indexed {} photos in {:.2f} seconds".format(num_photos, total_time)
        QMessageBox.information(self, "Indexing Results", message)
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoMetadataDatabase()
    window.show()
    sys.exit(app.exec_())

