import tempfile
import subprocess
import os


def dir_parser(directories,temp_dir):
    final_dir = []
    for path in directories:
        if temp_dir in path:
            temp_directory = os.path.relpath(path,temp_dir)
            final_dir.append(temp_directory) 
        
    return final_dir


def get_comment_to_code(url:str):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            subprocess.run(["git","clone","--depth","1","--single-branch",url,temp_dir],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                        )
        except subprocess.CalledProcessError:
            return None
        
        result = subprocess.run(
            ["cloc",temp_dir,"--json","--by-file"],
            capture_output=True,
            text = True
        )
        
        import json
        
        try:
            data = json.loads(result.stdout)
            data_for_file_struct = data.copy()
            del data_for_file_struct["header"]
            file_structure = data_for_file_struct.keys()
            file = dir_parser(file_structure,temp_dir)
            return data.get("SUM"),file
        except json.JSONDecodeError:
            return None
