import os
import json
import sqlite3


class DatabaseManager:
    def __init__(self, photo_folder=None):
        self.photo_folder = photo_folder


    def combine_tag_group_and_tag_name(self, tag_group, tag_name):
        # Return the tag name with the tag group name appended, separated by an underscore
        return f"{tag_group}_{tag_name}"

    def create_metadata_table(self):
        conn = sqlite3.connect(os.path.join(self.photo_folder, "photo_metadata.db"))
        c = conn.cursor()
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
                # full_column_name = self.combine_tag_group_and_tag_name(group, column_name)
                columns.append(f"[{column_name}] {data_type}")
        c.execute("CREATE TABLE IF NOT EXISTS photo_metadata (" + ",".join(columns) + ")")
        conn.commit()
        conn.close()

    def load_column_map(self):
        with open(os.path.join(os.path.dirname(__file__), "tags.json"), "r") as f:
            try:
                column_map = {}
                metadata_tags = json.load(f)["metadata_tags"]
                for tag_group, tags in metadata_tags.items():
                    for tag_name, _ in tags.items():
                        sanitized_tag_name = tag_name.replace("-", "_")
                        column_map[f"{tag_group}_{sanitized_tag_name}"] = f"{tag_group}_{tag_name}"
                column_map["SourceFile"] = "SourceFile"
                return column_map
            except json.JSONDecodeError as e:
                error_message = f"Error decoding tags JSON file: {e}"
                with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f_err:
                    f_err.write(error_message + "\n")
                return None

    def get_column_names(self, cursor):
        cursor.execute("SELECT * FROM photo_metadata")
        column_names = [description[0] for description in cursor.description]
        if 'SourceFile' in column_names:
            column_names.remove('SourceFile')
        column_names.insert(0, 'SourceFile')
        return column_names

    def prepare_metadata_values(self, photo_metadata, metadata_tags):
        values = [str(photo_metadata["SourceFile"])]
        for group, tags in metadata_tags.items():
            for tag in tags:
                sanitized_tag = tag.replace("-", "_")
                value = photo_metadata.get(sanitized_tag, "")
                if isinstance(value, str):
                    value = value.strip()
                values.append(value)
        return values

    def insert_metadata_record(self, cursor, column_names, values):
        try:
            cursor.execute(
                f"INSERT INTO photo_metadata ({', '.join(column_names)}) VALUES ({', '.join(['?' for _ in range(len(column_names))])})",
                values)
        except sqlite3.Error as e:
            error_message = f"Error inserting metadata into database for file {values[0]}:\n"
            error_message += f"{e}"
            with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                f.write(error_message + "\n")

            # Print the problematic column name and value
            problem_index = 23 - 1  # Adjust for 0-based indexing
            print(f"Error: {error_message}")
            print(f"Problematic column: {column_names[problem_index]}, value: {values[problem_index]}")

    def insert_metadata_into_database(self, metadata):
        column_map = self.load_column_map()
        if column_map is None:
            return

        conn = sqlite3.connect(os.path.join(self.photo_folder, "photo_metadata.db"))
        c = conn.cursor()

        column_names = self.get_column_names(c)

        # Load the metadata_tags from the tags.json file
        with open(os.path.join(os.path.dirname(__file__), "tags.json"), "r") as f:
            try:
                metadata_tags = json.load(f)["metadata_tags"]
            except json.JSONDecodeError as e:
                error_message = f"Error decoding tags JSON file: {e}"
                with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f_err:
                    f_err.write(error_message + "\n")
                return

        for photo_metadata in metadata:
            values = self.prepare_metadata_values(photo_metadata, metadata_tags)
            self.insert_metadata_record(c, column_names, values)

        conn.commit()
        conn.close()





