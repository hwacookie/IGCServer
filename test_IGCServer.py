import pytest
import requests
import os
import tempfile
import zipfile
import IGCParser


BASE_URL = "http://localhost:8000"

@pytest.fixture
def uploaded_igc_file():
    """
    Fixture to upload an IGC file and return its filename.
    Cleans up by deleting the file after the test.
    """
    igc_content = """AXCT12345
HFDTEDATE:010125
HFPLTPILOTINCHARGE:Test Pilot
HOSITSite:Test Site
HFGTYGLIDERTYPE:Test Glider
B0800005000000N00000000EA
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.igc', delete=False, encoding='utf-8') as f:
        f.write(igc_content)
        temp_file = f.name
        filename = os.path.basename(temp_file)

    with open(temp_file, 'rb') as f:
        response = requests.post(f"{BASE_URL}/igc/upload", files={'file': (filename, f, 'application/octet-stream')}, allow_redirects=False)
    
    os.unlink(temp_file)
    assert response.status_code == 303

    yield filename
    
    # Cleanup
    requests.delete(f"{BASE_URL}/igc/{filename}", allow_redirects=False)


def test_list_igc_files():
    response = requests.get(f"{BASE_URL}/igc/")
    assert response.status_code == 200
    response.json()


def test_upload_igc_file():
    igc_content = """AXCT12345
HFDTEDATE:010125
HFPLTPILOTINCHARGE:Test Pilot
HOSITSite:Test Site
HFGTYGLIDERTYPE:Test Glider
B0800005000000N00000000EA
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.igc', delete=False, encoding='utf-8') as f:
        f.write(igc_content)
        temp_file = f.name
        filename = os.path.basename(temp_file)

    with open(temp_file, 'rb') as f:
        response = requests.post(f"{BASE_URL}/igc/upload", files={'file': (filename, f, 'application/octet-stream')}, allow_redirects=False)
    
    os.unlink(temp_file)
    assert response.status_code == 303 # Check for redirect
    
    # Verify upload by listing files
    response = requests.get(f"{BASE_URL}/igc/")
    files = response.json()
    uploaded_file = next((f for f in files if f['filename'] == filename), None)
    assert uploaded_file is not None
    assert uploaded_file['pilot'] == "Test Pilot"
    assert uploaded_file['datetime'] == "2025-01-01 08:00"
    assert uploaded_file['glider_model'] == "Test Glider"
    
    # Cleanup
    requests.delete(f"{BASE_URL}/igc/{filename}", allow_redirects=False)


def test_download_igc_file(uploaded_igc_file):
    filename = uploaded_igc_file
    response = requests.get(f"{BASE_URL}/igc/{filename}")
    assert response.status_code == 200
    assert len(response.content) > 0


def test_delete_igc_file():
    # Setup: upload a file to be deleted
    igc_content = "A"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.igc', delete=False, encoding='utf-8') as f:
        f.write(igc_content)
        temp_file = f.name
        filename = os.path.basename(temp_file)
    
    with open(temp_file, 'rb') as f:
        requests.post(f"{BASE_URL}/igc/upload", files={'file': (filename, f, 'application/octet-stream')})
    os.unlink(temp_file)

    # The actual test
    response = requests.delete(f"{BASE_URL}/igc/{filename}", allow_redirects=False)
    assert response.status_code == 303 # Check for redirect
    
    # Verify deletion
    response = requests.get(f"{BASE_URL}/igc/")
    files = response.json()
    assert not any(f['filename'] == filename for f in files)


def test_upload_zip_file():
    # Create a dummy ZIP with IGC files
    igc_content1 = """AXCT12345
HFDTEDATE:010125
HFPLTPILOTINCHARGE:Test Pilot 1
HOSITSite:Test Site 1
HFGTYGLIDERTYPE:Test Glider 1
B0800005000000N00000000EA
"""
    igc_content2 = """AXCT67890
HFDTEDATE:020125
HFPLTPILOTINCHARGE:Test Pilot 2
HOSITSite:Test Site 2
HFGTYGLIDERTYPE:Test Glider 2
B0800005000000N00000000EA
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
            response = requests.post(f"{BASE_URL}/igc/upload", files={'file': ('test.zip', f, 'application/zip')}, allow_redirects=False)

    assert response.status_code == 303 # Check for redirect

    # Verify upload by listing files
    response = requests.get(f"{BASE_URL}/igc/")
    files = response.json()
    info1 = next((i for i in files if i['filename'] == 'test1.igc'), None)
    info2 = next((i for i in files if i['filename'] == 'test2.igc'), None)
    assert info1 is not None
    assert info2 is not None
    assert info1['pilot'] == "Test Pilot 1"
    assert info1['date'] == "2025-01-01"
    assert info1['location'] == "Test Site 1"
    assert info1['glider_model'] == "Test Glider 1"
    assert info2['pilot'] == "Test Pilot 2"
    assert info2['date'] == "2025-01-02"
    assert info2['location'] == "Test Site 2"
    assert info2['glider_model'] == "Test Glider 2"
    
    # Cleanup
    requests.post(f"{BASE_URL}/igc/test1.igc/delete", allow_redirects=False)
    requests.post(f"{BASE_URL}/igc/test2.igc/delete", allow_redirects=False)


def test_skytraxx_parser():
    """Tests parsing of a SkyTraxx IGC file."""
    igc_content = """AXSX004 SKYTRAXX
HFPLTPILOT:Hauke
HFGTYGLIDERTYPE:Prion4
HFDTM100GPSDATUM:WGS-84
HFRFWFIRMWAREVERSION:202410141115
HFRHWHARDWAREVERSION:2.1
HFTZNTIMEZONE:+2.00
HFSITSITE:Buchenberg
HFDTE021025
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.igc', delete=False) as f:
        f.write(igc_content)
        temp_file = f.name
    
    headers = IGCParser.parse(temp_file)
    os.unlink(temp_file)
    
    assert headers['pilot'] == 'Hauke'
    assert headers['date'] == '2025-10-02'
    assert headers['location'] == 'Buchenberg'


def test_start_time_and_duration():
    """Tests that start_time and duration are correctly parsed and returned."""
    igc_content = """AXCT12345
HFDTEDATE:030125
HFPLTPILOTINCHARGE:Time Pilot
B0830005000000N00000000EA
B0830015000000N00000000EA
B0945155000000N00000000EA
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.igc', delete=False, encoding='utf-8') as f:
        f.write(igc_content)
        temp_file = f.name
        filename = os.path.basename(temp_file)

    with open(temp_file, 'rb') as f:
        response = requests.post(f"{BASE_URL}/igc/upload", files={'file': (filename, f, 'application/octet-stream')}, allow_redirects=False)
    
    os.unlink(temp_file)
    assert response.status_code == 303

    response = requests.get(f"{BASE_URL}/igc/")
    files = response.json()
    uploaded_file = next((f for f in files if f['filename'] == filename), None)
    
    assert uploaded_file is not None
    assert uploaded_file['pilot'] == "Time Pilot"
    assert uploaded_file['date'] == "2025-01-03"
    assert uploaded_file['start_time'] == "08:30:00"
    assert uploaded_file['duration'] == "1:15:15"
    
    # Clean up the created file
    requests.delete(f"{BASE_URL}/igc/{filename}", allow_redirects=False)