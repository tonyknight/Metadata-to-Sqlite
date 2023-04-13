import json
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QMessageBox, QPushButton, QProgressBar

from metadataLoader import MetadataLoader
from databaseManager import DatabaseManager

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
        self.progress_bar.setValue(0)  # Add this line to set the initial value to 0
        self.progress_bar.setMinimum(0)  # Add this line to set the minimum value to 0
        self.progress_bar.setMaximum(100)  # Add this line to set the maximum value to 100

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
        if not self.photo_folder:
            QMessageBox.warning(self, "Error", "Please select a folder first.")
            return

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

        # create the metadata table in the database
        self.database_manager.create_metadata_table()

        # dump metadata to a JSON file
        with open(os.path.join(self.photo_folder, "metadata.json"), "w") as f:
            json.dump(metadata, f)

        # insert the metadata into the database
        self.database_manager.insert_metadata_into_database(metadata)

        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Success", "Metadata added to the database successfully!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoMetadataDatabase()
    window.show()
    sys.exit(app.exec_())
