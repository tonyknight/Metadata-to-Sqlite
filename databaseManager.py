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

    def insert_metadata_into_database(self, metadata):
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
                with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f_err:
                    f_err.write(error_message + "\n")
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
        for photo_metadata in metadata:
            # Get the values from the photo_metadata dictionary
            values = []
            for group, tags in metadata_tags.items():
                for tag in tags:
                    sanitized_tag = tag.replace("-", "_")
                    value = photo_metadata.get(sanitized_tag, "")
                    if isinstance(value, str):
                        value = value.strip()
                    values.append(value)
            # Append the SourceFile value to the values list
            values.insert(0, str(photo_metadata["SourceFile"]))

            # Insert the metadata into the SQLite database
            try:
                c.execute(
                    f"INSERT INTO photo_metadata ({', '.join(column_names)}) VALUES ({', '.join(['?' for _ in range(len(column_names))])})",
                    values)
            except sqlite3.Error as e:
                error_occurred = False
                for i, column_name in enumerate(column_names):
                    try:
                        c.execute(
                            f"INSERT INTO photo_metadata ({column_name}) VALUES (?)",
                            (values[i],))
                    except sqlite3.Error as e:
                        error_occurred = True
                        error_message = f"Error inserting metadata into database for file {photo_metadata['SourceFile']}:\n"
                        error_message += f"\tColumn '{column_name}' with value {values[i]} ({type(values[i])}) caused the data type mismatch error."
                        with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                            f.write(error_message + "\n")
                        print(f"Error: {error_message}")

                if not error_occurred:
                    conn.commit()
                else:
                    conn.rollback()

                continue

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
