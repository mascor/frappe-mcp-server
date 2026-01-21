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

# Frappe MCP Server - Test Report

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

### Section A: Standard DocType Operations

| Test | DocType | Operation | Status |
|------|---------|-----------|--------|
| A1 | Note | create_doc | ✅ PASS |
| A2 | Note | get_doc | ✅ PASS |
| A3 | Note | update_doc | ✅ PASS |
| A4 | Note | search_docs | ✅ PASS |
| A5 | Note | delete_doc | ✅ PASS |
| A6 | Event | create_doc | ✅ PASS |
| A7 | Event | get_meta | ✅ PASS |
| A8 | Event | delete_doc | ✅ PASS |

### Section B: Filters and Fields

| Test | Description | Status |
|------|-------------|--------|
| B1 | search_docs with filters | ✅ PASS |
| B2 | search_docs with fields | ✅ PASS |
| B3 | search_docs with filters + fields | ✅ PASS |

### Section C: Edge Cases / Error Handling

| Test | Description | Expected | Status |
|------|-------------|----------|--------|
| C1 | get_doc non-existent document | 404 Not Found | ✅ PASS |
| C2 | create_doc missing required field | 417 Expectation Failed | ✅ PASS |
| C3 | update_doc non-existent document | 404 Not Found | ✅ PASS |
| C4 | delete_doc non-existent document | 404 Not Found | ✅ PASS |
| C5 | get_meta non-existent DocType | 403 Forbidden | ✅ PASS |

### Section D: Permissions

| Test | Description | Status |
|------|-------------|--------|
| D1 | search_docs on allowed DocType (User) | ✅ PASS |
| D2 | get_meta on non-allowed DocType (Role) | ✅ PASS (403) |

---

## 🎉 Final Result: 18/18 Tests Passed

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
      "options": "Open\\nClosed\\nCancelled",
      "reqd": 0,
      "default": "Open"
    },
    {
      "fieldname": "priority",
      "label": "Priority",
      "fieldtype": "Select",
      "options": "High\\nMedium\\nLow",
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
Search for documents with optional filters and fields.

**Request (basic):**
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

**Request (with filters and fields):**
```
doctype: "ToDo"
filters: {"status": "Open"}
fields: ["name", "status", "priority", "description"]
```

**Response:**
```json
[
  {
    "name": "todo001",
    "status": "Open",
    "priority": "Medium",
    "description": "Test task 1"
  },
  {
    "name": "todo002",
    "status": "Open",
    "priority": "High",
    "description": "Test task 2"
  }
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

**Error Response (document not found):**
```
HTTP 404 Not Found
```

---

## Setup Requirements

1. **Install the MCP Server app** on your Frappe site
   ```bash
   bench get-app https://github.com/[repo]/frappe-mcp-server
   bench --site [your-site] install-app mcp_server
   ```

2. **Create an API user** (e.g., `mcp_user@example.com`)

3. **Generate API keys** for the user
   - Go to User → API Access → Generate Keys

4. **Assign appropriate roles** to the API user (e.g., System Manager)

5. **Configure the Allowlist**
   - Go to "MCP Doctype Allowlist"
   - Add DocTypes you want to expose via MCP
   - Configure allowed operations (Read, Create, Update, Delete, Meta)

6. **Configure the MCP client** with the API credentials

---

## Allowlist Configuration

The MCP Server uses an Allowlist to control which DocTypes are accessible. For each DocType you can configure:

| Option | Description |
|--------|-------------|
| **Allow Read (Get, Search)** | Permits `get_doc` and `search_docs` |
| **Allow Create** | Permits `create_doc` |
| **Allow Update** | Permits `update_doc` |
| **Allow Delete** | Permits `delete_doc` |
| **Allow Meta (Schema)** | Permits `get_meta` |
| **Max Page Length** | Limits results for `search_docs` (0 = default) |
| **Allowed Fields (Read)** | Restrict which fields are returned (empty = all) |
| **Allowed Filters** | Restrict which fields can be used in filters (empty = all) |

---

## Error Codes

| HTTP Code | Meaning | Common Causes |
|-----------|---------|---------------|
| `200` | Success | Operation completed |
| `403` | Forbidden | DocType not in Allowlist or operation not permitted |
| `404` | Not Found | Document or DocType does not exist |
| `417` | Expectation Failed | Validation error (e.g., missing required field) |
| `500` | Internal Server Error | Server-side error (check logs) |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` on all calls | Missing Allowlist entry | Add DocType to MCP Doctype Allowlist |
| `403 Forbidden` on specific operation | Operation not enabled | Enable the operation in Allowlist |
| `403 Forbidden` with filters | Filter field not allowed | Add field to Allowed Filters or leave empty for all |
| `404 Not Found` | Document doesn't exist | Verify document name |
| `417 Expectation Failed` | Validation error | Check required fields in DocType |
| `500 Internal Server Error` | Code error | Run `bench --site [site] logs` |

---

## Security Notes

- Only DocTypes explicitly added to the Allowlist are accessible
- Each operation (Read, Create, Update, Delete, Meta) must be explicitly enabled
- API authentication is required for all operations
- Consider restricting sensitive DocTypes (User, Role, etc.) in production