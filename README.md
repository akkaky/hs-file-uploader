# HubSpot File Uploader

This simple Python script is designed to uploading files to HubSpot using its API.

## Prerequisites

- Python 3.10 or higher

## Setup

1. Clone the repository or download the script directly.
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Before running the script, ensure you have a HubSpot API access token. If you don't have one yet:

1. Visit the [HubSpot API](https://developers.hubspot.com/docs/api/overview) to get your API key.
2. Set the obtained API key either by:
    - Modifying the `HS_TOKEN` variable in the script.
    - Exporting it as an environment variable: `export HS_TOKEN=your_access_token`.

## Usage

Run the script using the command line with the following arguments:

```bash
python hs_file_uploader.py -s <source_path> -d <destination_folder>
```

| Argument          | Description                                                          |
|-------------------|----------------------------------------------------------------------| 
| -s, --source      | Path to the folder or file you want to upload.                       |
| -d, --destination | Destination folder on the HubSpot file manager. Default path is "/". |

## Example

```bash
python hs_file_uploader.py -s /path/to/local/folder -d /remote/folder
```

## Important Notes

- This script excludes certain files and directories by default (e.g., .DS_Store, .git, .idea, node_modules), which will
  not be uploaded.
- It supports asynchronous file uploading using multiple workers for efficiency. If a lot of 429 response status codes
  decrease count of workers

Feel free to modify the exclusion lists and adjust the worker count in the script as per your requirements.

For more information, refer to the [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview).
