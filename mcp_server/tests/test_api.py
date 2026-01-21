import frappe
from frappe.tests.utils import FrappeTestCase
from mcp_server.api import mcp_ping, search_docs, get_doc, create_doc, update_doc
from mcp_server.utils import get_mcp_settings

class TestMCPAPI(FrappeTestCase):
    def setUp(self):
        # Clear Singles for Settings
        frappe.db.sql("DELETE FROM `tabSingles` WHERE doctype='MCP Server Settings'")
        
        # Clear regular tables
        frappe.db.delete("MCP Doctype Allowlist")
        frappe.db.delete("MCP Audit Log")
        
        # Setup Settings
        self.settings = frappe.get_single("MCP Server Settings")
        self.settings.enabled = 1
        self.settings.auth_mode = "Token"
        self.settings.mcp_user = "Administrator" # Use admin for test convenience or create one
        self.settings.token_secret = "test-secret"
        self.settings.save()
        
        # Setup Allowlist for User
        self.allowlist = frappe.get_doc({
            "doctype": "MCP Doctype Allowlist",
            "doctype_ref": "ToDo",
            "allow_read": 1,
            "allow_create": 1,
            "allow_update": 1,
            "allow_delete": 1,
            "allow_meta": 1
        }).insert()
        
        # Mock Request Header
        frappe.request = frappe.Mock()
        frappe.request.headers = {"X-MCP-Token": "test-secret"}
        frappe.local.request = frappe.request
        
    def test_ping(self):
        res = mcp_ping()
        self.assertEqual(res["status"], "ok")
        
    def test_auth_fail(self):
        frappe.request.headers = {"X-MCP-Token": "wrong"}
        with self.assertRaises(frappe.AuthenticationError):
             mcp_ping()
             
    def test_search_docs(self):
        # Create a ToDo
        todo = frappe.get_doc({"doctype": "ToDo", "description": "MCP Test"}).insert()
        
        res = search_docs("ToDo", filters={"description": "MCP Test"})
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].name, todo.name)
        
    def test_create_doc(self):
        data = {"description": "Created by MCP"}
        # Must whitelist field 'description'? 
        # By default in my impl: if allowed_fields_write is empty -> Allow all? 
        # or Allow None?
        # My impl in utils.py:
        # if is_strict: ... else: allow all valid fields.
        # My allowlist setup has empty tables -> Allow all.
        
        res = create_doc("ToDo", data)
        self.assertEqual(res["description"], "Created by MCP")
        
    def test_not_allowed_doctype(self):
        with self.assertRaises(frappe.PermissionError):
            search_docs("User")
            
    def test_audit_logging(self):
        mcp_ping()
        logs = frappe.get_all("MCP Audit Log", fields=["name", "operation", "status"])
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0].status, "Success")

