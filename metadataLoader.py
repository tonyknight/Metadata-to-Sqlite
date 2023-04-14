import json
import os
import subprocess


class MetadataLoader:
    def __init__(self, photo_folder):
        self.photo_folder = photo_folder

    def load_metadata(self):
        cmd = self.get_exiftool_command()
        metadata_json = self.run_exiftool_command(cmd)
        if not metadata_json:
            return None
        metadata = self.convert_metadata_json_to_list(metadata_json)
        return metadata

    def run_exiftool_command(self, cmd):
        command_file_path = os.path.join(self.photo_folder, "exiftool_command.txt")
        with open(command_file_path, "w") as f:
            f.write(" ".join(cmd))

        with open(command_file_path, "r") as f:
            exiftool_command = f.read().strip()

        print("Exiftool command: ", exiftool_command)

        try:
            metadata_json_bytes = subprocess.check_output(exiftool_command, shell=True)
            metadata_json_str = metadata_json_bytes.decode("utf-8")
            metadata_json = json.loads(metadata_json_str)
            with open(os.path.join(self.photo_folder, "metadata.json"), "w") as f:
                json.dump(metadata_json, f)
            return metadata_json
        except subprocess.CalledProcessError as e:
            error_message = f"Error running Exiftool command: {e}"
            with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                f.write(error_message + "\n")
            return None

    def convert_metadata_json_to_list(self, metadata_json):
        try:
            with open(os.path.join(os.path.dirname(__file__), "tags.json"), "r") as f:
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
            return metadata_list
        except json.JSONDecodeError as e:
            error_message = f"Error decoding JSON: {e}"
            with open(os.path.join(self.photo_folder, "errors.txt"), "a") as f:
                f.write(error_message + "\n")
            return []

    def get_exiftool_command(self):
        with open(os.path.join(os.path.dirname(__file__), "tags.json"), "r") as f:
            metadata_tags = json.load(f)["metadata_tags"]
        groups = ["exif", "iptc", "xmp"]
        metadata_tags_str = " ".join([f"-{group}:{key}" for group in groups for key in metadata_tags[group]])

        exclude_file_types = [".txt", ".csv", ".db", ".args", ".json"]
        exclude_filter = " ".join([f"--ext {file_type}" for file_type in exclude_file_types])
        command = ['exiftool', '-m 2000m', '-r', '-progress', '-j', exclude_filter, metadata_tags_str, f'"{self.photo_folder}"']

        command_file_path = os.path.join(self.photo_folder, "exiftool_command.txt")
        with open(command_file_path, "w") as f:
            f.write(" ".join(command))

        return command
