import os
import sys
import json
import sqlite3
import re
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
        # Define a callback function to update the progress bar
        def progress_callback(percentage, status):
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(status)

        # get the metadata for all photos in the folder
        cmd = self._get_exiftool_command()
        metadata_json = self._run_exiftool_command(cmd, progress_callback=progress_callback)

        # get the metadata for all photos in the folder
        cmd = self._get_exiftool_command()
        metadata_json = self._run_exiftool_command(cmd)
        if not metadata_json:
            error_message = "Error: Could not retrieve metadata for photos in the selected folder."
            with open(os.path.join(self.photo_folder, "Errors.txt"), "w") as f:
                f.write(error_message)
            with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                f.write(error_message + "\n")
            QMessageBox.critical(self, "Error", error_message)
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

    def _run_exiftool_command(self, cmd, progress_callback=None):
        command_file_path = os.path.join(self.photo_folder, "exiftool_command.txt")
        with open(command_file_path, "w") as f:
            f.write(" ".join(cmd))

        with open(command_file_path, "r") as f:
            exiftool_command = f.read().strip()

        print("Exiftool command: ", exiftool_command)

        try:
            # Use Popen instead of check_output to get the process object
            process = subprocess.Popen(
                exiftool_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                universal_newlines=True
            )

            # Use tqdm to wrap the output and provide a progress bar
            with tqdm(total=100, file=sys.stdout, desc="Processing photos") as pbar:
                for line in process.stdout:
                    # Update the progress bar if the line contains a percentage
                    if " %" in line:
                        percentage = int(line.split(" %")[0].split(" ")[-1])
                        status = line.strip()
                        pbar.update(percentage - pbar.n)
                        pbar.set_description(status)
                        if progress_callback is not None:
                            progress_callback(percentage, status)

            # Check if the process exited successfully
            if process.returncode != 0:
                error_message = f"Error running Exiftool command: {process.stderr.read()}"
                with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                    f.write(error_message + "\n")
                QMessageBox.critical(self, "Error", error_message)
                return None

            metadata_json_str = process.communicate()[0]
            metadata_json = json.loads(metadata_json_str)
            with open(os.path.join(self.photo_folder, "metadata.json"), "w") as f:
                json.dump(metadata_json, f)
            return metadata_json
        except subprocess.CalledProcessError as e:
            error_message = f"Error running Exiftool command: {e}"
            with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                f.write(error_message + "\n")
            QMessageBox.critical(self, "Error", error_message)
            return None

    def _convert_metadata_json_to_list(self, metadata_json):
        try:
            with open('tags.json', 'r') as f:
                tags = json.load(f)
            metadata_list = []
            for metadata_obj in metadata_json:
                metadata = {}
                for key in metadata_obj:
                    if key in tags:
                        metadata[tags[key]] = metadata_obj[key]
                    else:
                        metadata[key] = metadata_obj[key]
                metadata_list.append(metadata)
                # print out the values of the metadata dictionary for debugging
                print(metadata)
            return metadata_list
        except json.JSONDecodeError as e:
            error_message = f"Error decoding JSON: {e}"
            with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                f.write(error_message + "\n")
            QMessageBox.critical(self, "Error", error_message)
            return []

    def _create_metadata_table(self, cursor):
        with open(os.path.join(os.path.dirname(__file__), "tags.json"), "r") as f:
            metadata_tags = json.load(f)
            exif_tags = metadata_tags["metadata_tags"]["exif"]
            iptc_tags = metadata_tags["metadata_tags"]["iptc"]
            xmp_tags = metadata_tags["metadata_tags"]["xmp"]

        # Create the SQLite table dynamically based on the metadata tags defined in the tags.json file
        columns = ["[SourceFile] TEXT"]
        for group, tags in [("exif", exif_tags), ("iptc", iptc_tags), ("xmp", xmp_tags)]:
            for name in tags:
                data_type, column_name = tags[name]
                full_column_name = self._combine_tag_group_and_tag_name(group, column_name)
                columns.append(f"[{column_name}] {data_type.upper()}")
        cursor.execute("CREATE TABLE IF NOT EXISTS photo_metadata (" + ",".join(columns) + ")")

    def _combine_tag_group_and_tag_name(self, tag_group, tag_name):
        # Return the tag name with the tag group name appended, separated by an underscore
        return f"{tag_group}_{tag_name}"

    def _insert_metadata_into_database(self, metadata):
        # Load the column map from the tags.json file
        with open(os.path.join(os.path.dirname(__file__), "tags.json"), "r") as f:
            try:
                column_map = {}
                metadata_tags = json.load(f)["metadata_tags"]
                for tag_group, tags in metadata_tags.items():
                    for tag_name, _ in tags.items():
                        sanitized_tag_name = tag_name.replace("-", "_")
                        column_map[f"{tag_group}_{sanitized_tag_name}"] = f"{tag_group}_{tag_name}"
            except json.JSONDecodeError as e:
                error_message = f"Error decoding tags JSON file: {e}"
                with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                    f.write(error_message + "\n")
                QMessageBox.critical(self, "Error", error_message)
                return

        # Append SourceFile to the column_map
        column_map["SourceFile"] = "SourceFile"

        # Inserts the photo metadata into the SQLite database.
        conn = sqlite3.connect(os.path.join(self.photo_folder, "photo_metadata.db"))
        c = conn.cursor()

        # Get the column names to use in the insert statement
        c.execute("SELECT * FROM photo_metadata")
        column_names = [description[0] for description in c.description]

        # Loop through the metadata and insert it into the SQLite database
        self.progress_bar.setMaximum(len(metadata))
        for i, photo_metadata in enumerate(tqdm(metadata)):
            # Get the values from the photo_metadata dictionary
            values = []
            problematic_tags = []
            for group, tags in metadata_tags.items():
                for tag in tags:
                    column_name = f"{group}_{tag}"
                    sanitized_tag = tag.replace("-", "_")
                    value = photo_metadata.get(sanitized_tag, "")
                    if isinstance(value, str):
                        # Replace illegal characters in the value with underscores
                        value = re.sub(r"[^\w\d_]+", "_", value)
                        if value != photo_metadata.get(sanitized_tag, ""):
                            problematic_tags.append(sanitized_tag)
                    values.append(value)

            # Append the SourceFile value to the values list
            values.insert(0, photo_metadata["SourceFile"])

            # Insert the metadata into the SQLite database
            try:
                c.execute(
                    f"INSERT INTO photo_metadata ({', '.join(column_names)}) VALUES ({', '.join(['?' for _ in range(len(column_names))])})",
                    values)

            except sqlite3.Error as e:
                error_message = f"Error inserting metadata into database: {e}"
                with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                    f.write(error_message + "\n")
                    f.write(f"Problematic tags: {problematic_tags}\n")
                print(f"Error: {error_message}")
                print(
                    f"SQL statement: INSERT INTO photo_metadata ({column_names}) VALUES ({','.join(['?'] * len(column_names))})")
                continue

            self.progress_bar.setValue(i + 1)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

    def _get_exiftool_command(self):
        with open(os.path.join(os.path.dirname(__file__), "tags.json"), "r") as f:
            metadata_tags = json.load(f)["metadata_tags"]
        groups = ["exif", "iptc", "xmp"]
        metadata_tags_str = " ".join([f"-{group}:{key}" for group in groups for key in metadata_tags[group]])

        # Exclude certain file types from being processed
        exclude_file_types = [".txt", ".csv", ".db", ".args", ".json"]
        exclude_filter = " ".join([f"--ext {file_type}" for file_type in exclude_file_types])
        command = ['exiftool', '-r', '-progress', '-j', exclude_filter, metadata_tags_str, f'"{self.photo_folder}"']

        command_file_path = os.path.join(self.photo_folder, "exiftool_command.txt")
        with open(command_file_path, "w") as f:
            f.write(" ".join(command))

        return command


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoMetadataDatabase()
    window.show()
    sys.exit(app.exec_())
