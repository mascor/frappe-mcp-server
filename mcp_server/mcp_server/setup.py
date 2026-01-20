import frappe
from frappe import _

def setup_mcp(user_email="mcp@local", create_user=True):
    """
    Onboarding script to setup MCP Server.
    1. Creates MCP User if not exists.
    2. Assigns minimal role (if needed).
    3. Initializes MCP Server Settings.
    """
    if create_user:
        if not frappe.db.exists("User", user_email):
            user = frappe.new_doc("User")
            user.email = user_email
            user.first_name = "MCP"
            user.last_name = "User"
            user.send_welcome_email = 0
            user.params["ignore_password_policy"] = 1 # Hacky but sometimes needed
            user.insert(ignore_permissions=True)
            print(f"Created user {user_email}")
        else:
            print(f"User {user_email} already exists")
            
    # Settings
    settings = frappe.get_single("MCP Server Settings")
    settings.enabled = 1
    settings.auth_mode = "Token"
    settings.mcp_user = user_email
    
    if not settings.token_secret:
        settings.token_secret = frappe.generate_hash(length=32)
        print(f"Generated new Token Secret: {settings.token_secret}")
    else:
        print(f"Token Secret already set: {settings.token_secret}")
        
    settings.save(ignore_permissions=True)
    print("MCP Server Settings configured.")

    # Initialize Allowlist (Empty)
    # Nothing to do, it's empty by default.
