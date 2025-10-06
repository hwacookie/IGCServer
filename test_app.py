import requests
import os
import tempfile

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

if __name__ == "__main__":
    print("Testing IGCServer API...")
    initial_files = test_list_igc_files()
    filename = test_upload_igc_file()
    test_list_igc_files()
    test_download_igc_file(filename)
    test_delete_igc_file(filename)
    final_files = test_list_igc_files()
    assert len(final_files) == len(initial_files)
    print("All tests passed!")