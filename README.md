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

# Frappe MCP Server - Test Results

## Available Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `ping` | Check server connection | None |
| `search_docs` | Search documents | `doctype` (required), `filters` (optional), `fields` (optional) |
| `get_doc` | Get a specific document | `doctype` (required), `name` (required) |
| `create_doc` | Create a new document | `doctype` (required), `data` (required) |
| `update_doc` | Update an existing document | `doctype` (required), `name` (required), `data` (required) |
| `get_meta` | Get DocType metadata | `doctype` (required) |
| `delete_doc` | Delete a document | `doctype` (required), `name` (required) |

---

## Test Results Summary

| Command | Status | Notes |
|---------|--------|-------|
| `ping` | ✅ Pass | Server responds correctly |
| `get_meta` | ✅ Pass | Returns DocType structure |
| `create_doc` | ✅ Pass | Document created successfully |
| `search_docs` | ✅ Pass | Returns list of documents |
| `get_doc` | ✅ Pass | Returns document details |
| `update_doc` | ✅ Pass | Document updated successfully |
| `delete_doc` | ✅ Pass | Document deleted successfully |

---

## Test Examples

### 1. ping
Check server connection status.

**Response:**
```json
{
  "status": "ok",
  "site": "your-site.example.com",
  "user": "mcp_user@example.com"
}
```

---

### 2. get_meta
Get the structure of a DocType.

**Request:**
```
doctype: "ToDo"
```

**Response:**
```json
{
  "doctype": "ToDo",
  "fields": [
    {
      "fieldname": "status",
      "label": "Status",
      "fieldtype": "Select",
      "options": "Open\nClosed\nCancelled",
      "reqd": 0,
      "default": "Open"
    },
    {
      "fieldname": "priority",
      "label": "Priority",
      "fieldtype": "Select",
      "options": "High\nMedium\nLow",
      "reqd": 0,
      "default": "Medium"
    },
    {
      "fieldname": "date",
      "label": "Due Date",
      "fieldtype": "Date",
      "reqd": 0,
      "default": "Today"
    },
    {
      "fieldname": "description",
      "label": "Description",
      "fieldtype": "Text Editor",
      "reqd": 1
    }
  ],
  "issingle": 0,
  "istable": 0
}
```

---

### 3. create_doc
Create a new document.

**Request:**
```
doctype: "ToDo"
data: {
  "status": "Open",
  "priority": "High",
  "description": "Test task created via MCP"
}
```

**Response:**
```json
{
  "name": "abc123xyz",
  "owner": "mcp_user@example.com",
  "creation": "2026-01-21 10:18:41.295624",
  "modified": "2026-01-21 10:18:41.295624",
  "modified_by": "mcp_user@example.com",
  "docstatus": 0,
  "status": "Open",
  "priority": "High",
  "date": "2026-01-21",
  "description": "Test task created via MCP",
  "doctype": "ToDo"
}
```

---

### 4. search_docs
Search for documents.

**Request:**
```
doctype: "ToDo"
```

**Response:**
```json
[
  {"name": "todo001"},
  {"name": "todo002"},
  {"name": "todo003"}
]
```

---

### 5. get_doc
Get a specific document by name.

**Request:**
```
doctype: "ToDo"
name: "abc123xyz"
```

**Response:**
```json
{
  "name": "abc123xyz",
  "owner": "mcp_user@example.com",
  "status": "Open",
  "priority": "High",
  "date": "2026-01-21",
  "description": "Test task created via MCP",
  "creation": "2026-01-21 10:18:41.295624",
  "modified": "2026-01-21 10:18:41.295624",
  "modified_by": "mcp_user@example.com",
  "docstatus": 0
}
```

---

### 6. update_doc
Update an existing document.

**Request:**
```
doctype: "ToDo"
name: "abc123xyz"
data: {
  "status": "Closed",
  "priority": "Low"
}
```

**Response:**
```json
{
  "name": "abc123xyz",
  "owner": "mcp_user@example.com",
  "creation": "2026-01-21 10:18:41.295624",
  "modified": "2026-01-21 10:18:59.096886",
  "modified_by": "mcp_user@example.com",
  "docstatus": 0,
  "status": "Closed",
  "priority": "Low",
  "date": "2026-01-21",
  "description": "Test task created via MCP",
  "doctype": "ToDo"
}
```

---

### 7. delete_doc
Delete a document.

**Request:**
```
doctype: "ToDo"
name: "abc123xyz"
```

**Response:**
```json
{
  "status": "deleted",
  "name": "abc123xyz"
}
```

---

## Setup Requirements

1. **Install the MCP Server app** on your Frappe site
2. **Create an API user** (e.g., `mcp_user@example.com`)
3. **Generate API keys** for the user (User → API Access → Generate Keys)
4. **Assign appropriate roles** to the API user (e.g., System Manager)
5. **Configure the MCP client** with the API credentials

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` | Missing permissions | Assign roles to API user or add `@frappe.whitelist()` decorator |
| `417 Expectation Failed` | Module not found | Install/reinstall the MCP Server app |
| `500 Internal Server Error` | Code error | Check server logs with `bench --site [site] logs` |