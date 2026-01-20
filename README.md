# MCP Server for Frappe

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
bench --site <your-site> execute mcp_server.mcp_server.setup.setup_mcp
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
Include the `X-MCP-Token` header in all requests.

### Tools

#### `mcp_ping`
Health check and version info.
```bash
curl -X POST https://<yoursite>/api/method/mcp_server.api.mcp_ping \
     -H "X-MCP-Token: <your-token>"
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

## Quick Connect: MCP Client (Bridge)

To using this server with an AI Client (like Claude Desktop or Cursor), you need to run a local "bridge" script that forwards MCP requests to your Frappe site.

1.  **Install dependencies**:
    ```bash
    pip install "mcp[cli]" httpx
    ```

2.  **Create `frappe_mcp_bridge.py`**:
    ```python
    from mcp.server.fastmcp import FastMCP
    import httpx

    # Configuration
    FRAPPE_URL = "https://<your-site>"
    MCP_TOKEN = "<your-token>"

    mcp = FastMCP("Frappe Bridge")

    @mcp.tool()
    def search_docs(doctype: str, filters: dict = None, fields: list = None):
        """Search for documents in Frappe"""
        url = f"{FRAPPE_URL}/api/method/mcp_server.api.search_docs"
        resp = httpx.post(url, headers={"X-MCP-Token": MCP_TOKEN}, 
                         json={"doctype": doctype, "filters": filters, "fields": fields})
        resp.raise_for_status()
        return resp.json()["message"]

    @mcp.tool()
    def create_doc(doctype: str, data: dict):
        """Create a document in Frappe"""
        url = f"{FRAPPE_URL}/api/method/mcp_server.api.create_doc"
        resp = httpx.post(url, headers={"X-MCP-Token": MCP_TOKEN}, 
                         json={"doctype": doctype, "data": data})
        resp.raise_for_status()
        return resp.json()["message"]

    # Add other tools (get_doc, update_doc, etc.) similarly...

    if __name__ == "__main__":
        mcp.run()
    ```

3.  **Run it via your MCP Client Config**:
    Add this to your `claude_desktop_config.json`:
    ```json
    {
      "mcpServers": {
        "frappe": {
          "command": "python",
          "args": ["/path/to/frappe_mcp_bridge.py"]
        }
      }
    }
    ```