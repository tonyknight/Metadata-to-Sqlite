import json
import os
import sys
import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QMessageBox, QPushButton, QProgressBar

from metadataLoader import MetadataLoader
from databaseManager import DatabaseManager

class PhotoMetadataDatabase(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Photo Metadata Database")
        self.setGeometry(100, 100, 1024, 1024)

        self.folder_label = QLabel("", self)
        self.folder_label.setGeometry(50, 50, self.width() - 100, 50)
        self.folder_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, self.folder_label.height() + 100, self.width() - 100, 50)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        open_folder_button = QPushButton("Open Folder", self)
        open_folder_button.resize(200, 50)
        open_folder_button.clicked.connect(self.select_folder)

        open_json_file_button = QPushButton("Open JSON File", self)
        open_json_file_button.resize(200, 50)
        open_json_file_button.clicked.connect(self.select_json_file)

        self.create_db_button = QPushButton("Create Database", self)
        self.create_db_button.setEnabled(False)
        self.create_db_button.resize(200, 50)
        self.create_db_button.clicked.connect(self.start_database_creation)

        button_width = 200
        button_x = (self.width() - (3 * button_width + 20)) / 2
        open_folder_button.move(button_x, self.height() - open_folder_button.height() - 50)
        open_json_file_button.move(button_x + button_width + 10, self.height() - open_json_file_button.height() - 50)
        self.create_db_button.move(button_x + 2 * button_width + 20,
                                   self.height() - self.create_db_button.height() - 50)

        self.photo_folder = None
        self.json_file = None

    def select_json_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)",
                                              options=options)
        if file:
            # Rename the original JSON file
            original_file = os.path.splitext(file)[0] + "_original.json"
            os.rename(file, original_file)

            # Sanitize the JSON file
            try:
                self.sanitize_json_tags(original_file, file)
                QMessageBox.information(self, "Success", "Hyphens in tag names have been replaced with underscores.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred during JSON sanitization: {e}")
                return

            self.json_file = file
            self.folder_label.setText(self.json_file)
            self.create_db_button.setEnabled(True)


    def sanitize_json_tags(self, file_path, output_file_path):
        with open(file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
            for line in infile:
                outfile.write(
                    re.sub(r'("[-A-Za-z0-9]+)-([A-Za-z0-9]+":)', lambda m: m.group(1) + '_' + m.group(2), line))

    def select_folder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", options=options)
        if folder:
            self.photo_folder = folder
            self.folder_label.setText(self.photo_folder)
            self.create_db_button.setEnabled(True)

    def start_database_creation(self):
        if self.photo_folder is None and self.json_file is None:
            QMessageBox.warning(self, "Error", "Please select a folder or a JSON file first.")
            return

        if self.photo_folder is not None:
            # create instances of MetadataLoader and DatabaseManager classes
            self.metadata_loader = MetadataLoader(self.photo_folder)
            self.database_manager = DatabaseManager(self.photo_folder)

            metadata_json = self.metadata_loader.load_metadata()
            if not metadata_json:
                error_message = "Error: Could not retrieve metadata for photos in the selected folder."
                with open(os.path.join(self.photo_folder, "Errors.txt"), "w") as f:
                    f.write(error_message)
                with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                    f.write(error_message + "\n")
                QMessageBox.critical(self, "Error", error_message)
                return

            metadata = self.metadata_loader.convert_metadata_json_to_list(metadata_json)

        else:
            with open(self.json_file, "r") as f:
                metadata = json.load(f)

            self.database_manager = DatabaseManager(os.path.dirname(self.json_file))

        # create the metadata table in the database
        self.database_manager.create_metadata_table()

        # insert the metadata into the database
        self.database_manager.insert_metadata_into_database(metadata)

        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Success", "Metadata added to the database successfully!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoMetadataDatabase()
    window.show()
    sys.exit(app.exec_())
