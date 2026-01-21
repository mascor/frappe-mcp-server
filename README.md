# MCP Server for Frappe

[![Leggi in Italiano](https://img.shields.io/badge/lang-it-green.svg)](README.it.md)

A secure, audit-logged **Model Context Protocol (MCP)** server for Frappe. 
This app allows you to expose specific DocTypes and operations to MCP clients (like AI agents) with strict granular permissions, ensuring secure and controlled access to your Frappe data.

## Features

- **Secure Authentication**: dedicated `MCP User` access via Token or API Key.
- **Granular Allowlist**: Explicitly allow specific DocTypes and operations (Create, Read, Update, Delete).
- **Field-Level Control**: Restrict which fields can be read or written.
- **Audit Logging**: Every request is logged with latency, status, and payload summaries.
- **Strict Validation**: All filters and inputs are validated against the allowlist.

## Installation

1.  Get the app:
    ```bash
    bench get-app https://github.com/mascor/frappe-mcp-server
    ```

2.  Install on your site:
    ```bash
    bench --site <your-site> install-app mcp_server
    ```

## Configuration

### 1. Setup MCP User & Settings
You can use the included setup script to quickly configure the server with a default user and token:

```bash
bench --site <your-site> execute mcp_server.setup.setup_mcp
```
This will:
- Create a user `mcp@example.com` (if not exists).
- Generate a secure `X-MCP-Token` and save it in **MCP Server Settings**.
- Enable the MCP Server.

Alternatively, go to **MCP Server Settings** in Desk and configure manually.

### 2. Configure Allowlist
By default, **no access is allowed**. You must explicitly allow DocTypes.

1.  Go to **MCP Doctype Allowlist**.
2.  Create a new record for the DocType you want to expose (e.g., `ToDo`).
3.  Check the operations you want to allow (`Allow Read`, `Allow Create`, etc.).
4.  (Optional) restricting fields and filters in the child tables for tighter security.

## Usage

The server exposes standard MCP tools via the API.

### Authentication
The server supports **API Key** authentication (recommended for MCP clients).

Include the `Authorization` header in all requests.

### Tools

#### `mcp_ping`
Health check and version info.
```bash
curl -X POST https://<yoursite>/api/method/mcp_server.api.ping \
     -H "Authorization: token <api_key>:<api_secret>"
```

#### `search_docs`
Search for documents with filters.
```json
{
    "doctype": "ToDo",
    "filters": {"status": "Open"}
}
```

#### `create_doc`
Create a new document.
```json
{
    "doctype": "ToDo",
    "data": {
        "description": "New Task from MCP"
    }
}
```

#### `update_doc`
Update an existing document.
```json
{
    "doctype": "ToDo",
    "name": "TODO-0001",
    "data": {
        "status": "Closed"
    }
}
```

## Audit Log
Check **MCP Audit Log** in Desk to see a history of all requests, including success/failure status, latency, and diffs.

## License
MIT

## Quick Connect: MCP Client

To connect to this server from an AI Client (like Claude Desktop or Cursor), use the official Python Client:

[**frappe-mcp-client**](https://github.com/mascor/frappe-mcp-client)

Follow the installation and setup instructions in the client repository to get started.