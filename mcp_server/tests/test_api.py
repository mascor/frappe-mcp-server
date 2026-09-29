import frappe
from frappe.tests.utils import FrappeTestCase
from mcp_server.api import mcp_ping, search_docs, get_doc, create_doc, update_doc, delete_doc
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
            "allow_meta": 1,
            # "description" isn't an indexed field, so with the tightened
            # default (see test_search_docs_unindexed_field_requires_allowlist
            # below) it needs an explicit rule to stay filterable.
            "allowed_filters": [
                {"fieldname": "description", "operator": "="},
            ],
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

    def test_search_docs_default_allows_equality_on_indexed_field(self):
        # No "Allowed Filters" rows at all: only "=" on an indexed field
        # (unique/search_index/Link/Select) should be allowed by default.
        # "status" is a Select on ToDo, so it qualifies.
        self.allowlist.allowed_filters = []
        self.allowlist.save()

        frappe.get_doc({"doctype": "ToDo", "description": "MCP Test 2", "status": "Open"}).insert()
        res = search_docs("ToDo", filters={"status": "Open"})
        self.assertTrue(len(res) >= 1)

    def test_search_docs_default_rejects_unindexed_field(self):
        # "description" is a Text Editor field (not indexed): with no
        # explicit "Allowed Filters" rows it must be rejected, not
        # silently allowed as it was before this fix.
        self.allowlist.allowed_filters = []
        self.allowlist.save()

        with self.assertRaises(frappe.PermissionError):
            search_docs("ToDo", filters={"description": "MCP Test"})

    def test_search_docs_default_rejects_non_equality_operator(self):
        self.allowlist.allowed_filters = []
        self.allowlist.save()

        with self.assertRaises(frappe.PermissionError):
            search_docs("ToDo", filters=[["status", "like", "Open%"]])
            
    def test_delete_doc_respects_permissions(self):
        # Smoke test only: Administrator bypasses permission checks anyway,
        # so this doesn't prove the ignore_permissions=True removal fixed
        # anything — it only proves the removal didn't break the happy
        # path. A real regression test needs a non-privileged mcp_user
        # fixture without delete rights on ToDo, which this PR doesn't add.
        todo = frappe.get_doc({"doctype": "ToDo", "description": "To be deleted"}).insert()
        res = delete_doc("ToDo", todo.name)
        self.assertEqual(res["status"], "deleted")
        self.assertFalse(frappe.db.exists("ToDo", todo.name))

    def test_audit_logging(self):
        mcp_ping()
        logs = frappe.get_all("MCP Audit Log", fields=["name", "operation", "status"])
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0].status, "Success")

