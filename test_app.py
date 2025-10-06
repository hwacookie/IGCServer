import requests
import os
import tempfile
import zipfile

BASE_URL = "http://localhost:8000"

def test_list_igc_files():
    response = requests.get(f"{BASE_URL}/igc/")
    assert response.status_code == 200
    files = response.json()
    print("List files:", files)
    return files

def test_upload_igc_file():
    # Create a dummy IGC file
    igc_content = """HFDTE01012025
HPILTPILOT:Test Pilot
B0100005100000N00000000EA
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.igc', delete=False) as f:
        f.write(igc_content)
        temp_file = f.name

    with open(temp_file, 'rb') as f:
        response = requests.post(f"{BASE_URL}/igc/", files={'file': f})
    os.unlink(temp_file)
    assert response.status_code == 200
    info = response.json()
    print("Uploaded file info:", info)
    return info['filename']

def test_download_igc_file(filename):
    response = requests.get(f"{BASE_URL}/igc/{filename}")
    assert response.status_code == 200
    print("Downloaded file content length:", len(response.content))

def test_delete_igc_file(filename):
    response = requests.post(f"{BASE_URL}/igc/{filename}/delete")
    assert response.status_code == 200
    print("Delete response:", response.json())

def test_upload_zip_file():
    # Create a dummy ZIP with IGC files
    igc_content1 = """HFDTE01012025
HPILTPILOT:Test Pilot 1
B0100005100000N00000000EA
"""
    igc_content2 = """HFDTE02012025
HPILTPILOT:Test Pilot 2
B0200005200000N00000000EA
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        igc1_path = os.path.join(temp_dir, 'test1.igc')
        igc2_path = os.path.join(temp_dir, 'test2.igc')
        with open(igc1_path, 'w') as f:
            f.write(igc_content1)
        with open(igc2_path, 'w') as f:
            f.write(igc_content2)
        zip_path = os.path.join(temp_dir, 'test.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(igc1_path, 'test1.igc')
            zipf.write(igc2_path, 'test2.igc')
        with open(zip_path, 'rb') as f:
            response = requests.post(f"{BASE_URL}/igc/upload-zip", files={'file': f})
    assert response.status_code == 200
    infos = response.json()
    print("Uploaded ZIP files info:", infos)
    return [info['filename'] for info in infos]

if __name__ == "__main__":
    print("Testing IGCServer API...")
    initial_files = test_list_igc_files()
    filename = test_upload_igc_file()
    zip_filenames = test_upload_zip_file()
    test_list_igc_files()
    test_download_igc_file(filename)
    test_delete_igc_file(filename)
    for fname in zip_filenames:
        test_delete_igc_file(fname)
    final_files = test_list_igc_files()
    assert len(final_files) == len(initial_files)
    print("All tests passed!")