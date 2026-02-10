# Check Point API QA Tester

A systematic automation tool designed to act as a Quality Assurance agent for Check Point Management API releases. It dynamically parses the API specification and executes exhaustive lifecycle tests for every command and parameter.

## Features

- **Dynamic Versioning**: Automatically detects the Management Server API version (e.g., v2.1) and fetches the corresponding documentation.
- **Ordered Lifecycle Testing**: Executes `add` -> `show` -> `set` -> `delete` for a clean and verifiable test flow.
- **Combinatorial Parameter Coverage**: Identifies mutually exclusive parameter groups and generates multiple test variants to cover 100% of the API surface.
- **Detailed Reporting**: Generates JSON reports with full request/response data for every test variant.

## Installation

```bash
git clone <repo-url>
cd cp_api_qa_tester
pip install -r requirements.txt
```

## Usage

Run the tester against a specific API section (e.g., "Network Objects"):

```bash
python api_qa_tester.py -m <MGMT_IP> -u <USERNAME> -p <PASSWORD> -s "Network Objects"
```

### Arguments

| Flag | Description |
| :--- | :--- |
| `-m, --management` | Management Server IP (required) |
| `-u, --user` | Username (default: `admin`) |
| `-p, --password` | Password (securely prompted if omitted) |
| `-s, --section` | API Section to test (default: `Network Objects`) |

## Output

- **Logs**: Detailed execution logs are stored in `logs/`.
- **Reports**: Test results for each variant are saved in `reports/qa_report_<version>.json`.

## Best Practices

> [!IMPORTANT]
> This tool creates and deletes many objects. It is strictly recommended for use in **Lab/QA environments** only. Do not run against production management servers.
