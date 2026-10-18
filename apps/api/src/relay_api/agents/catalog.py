AGENTS = [
    {
        "name": "request_router",
        "label": "Request router",
        "purpose": "Understand the request and identify missing context.",
        "tools": [],
        "stage": "interpret",
    },
    {
        "name": "account_agent",
        "label": "Account specialist",
        "purpose": "Read the authenticated customer's current plan.",
        "tools": ["read_account"],
        "stage": "evidence",
    },
    {
        "name": "billing_agent",
        "label": "Billing specialist",
        "purpose": "Reconcile the bill against verified line items.",
        "tools": ["read_billing"],
        "stage": "evidence",
    },
    {
        "name": "service_agent",
        "label": "Service specialist",
        "purpose": "Combine network diagnostics with normalized legacy subscriber data.",
        "tools": ["diagnose_service"],
        "stage": "evidence",
    },
    {
        "name": "action_controller",
        "label": "Action controller",
        "purpose": "Authorize, confirm, persist and verify a support-case action.",
        "tools": ["create_case_after_confirmation"],
        "stage": "deterministic",
    },
]
