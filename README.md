# IGCServer

IGCServer is a web server that provides a REST API for storing, managing, and retrieving IGC (International Gliding Commission) files. IGC files are flight logs from gliding activities, containing data such as pilot information, flight date, and GPS coordinates.

## Features

- **REST API**: Endpoints for listing, uploading, downloading, and deleting IGC files.
- **ZIP Upload**: Upload ZIP files containing multiple IGC files for batch processing.
- **Web Interface**: Simple web page to view and manage stored IGC files, with forms for single and ZIP uploads.
- **Metadata Extraction**: Automatically extracts pilot name, flight date, and starting location from IGC files.
- **File Storage**: Stores IGC files in a dedicated directory on the server, with duplicate overwriting.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd IGCServer
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the server:
   ```
   python app.py
   ```
   The server will start on `http://localhost:8000`.

2. Access the web interface:
   - Open `http://localhost:8000` in your browser to view and manage IGC files.

3. Use the REST API:
    - `GET /igc/`: List all stored IGC files with metadata.
    - `POST /igc/`: Upload a new IGC file (multipart/form-data).
    - `POST /igc/upload-zip`: Upload a ZIP file containing multiple IGC files (multipart/form-data).
    - `GET /igc/{filename}`: Download a specific IGC file.
    - `POST /igc/{filename}/delete`: Delete a specific IGC file.

4. Run tests:
   ```
   python test_app.py
   ```
   Make sure the server is running before running tests.

## API Documentation

The API is described in `api.yaml` (OpenAPI 3.0 specification). You can use tools like Swagger UI to visualize and test the API.

## Architecture

The application is built using FastAPI, a modern Python web framework. Key components:

- **app.py**: Main application file containing the FastAPI app, route definitions, and IGC file processing logic.
- **templates/index.html**: Jinja2 template for the web interface.
- **aerofiles**: Library used for parsing IGC files to extract metadata.
- **igc_storage/**: Directory where uploaded IGC files are stored.
- **test_app.py**: Simple test script using the `requests` library to verify API functionality.

The server uses asynchronous endpoints for better performance and supports file uploads with validation (only .igc and .zip files allowed). For ZIP uploads, files are extracted securely to a temporary directory, and all .igc files are moved to storage with duplicate overwriting. Metadata is extracted from IGC headers and the first GPS fix to provide basic flight information.

## Dependencies

- fastapi: Web framework
- uvicorn: ASGI server
- jinja2: Template engine
- aerofiles: IGC file parser
- python-multipart: Multipart form data support for FastAPI
- requests: HTTP client for testing
- pytest: Testing framework

## Git LFS

Large or binary files (e.g., IGC files) are tracked using Git LFS to keep the repository size manageable.