TRANSACTION_STATUS_CHOICES = [
    ("RJCT", "Rejected"),
    ("RCVD", "Received"),
    ("ACCP", "Accepted"),
    ("ACTC", "Accepted Technical Validation"),
    ("ACSP", "Accepted Settlement in Process"),
    ("ACSC", "Accepted Settlement Completed"),
    ("ACWC", "Accepted with Change"),
    ("ACWP", "Accepted with Processing"),
    ("ACCC", "Accepted Credit Confirmation"),
    ("CANC", "Cancelled"),
    ("PDNG", "Pending"),
]

ACTION_CHOICES = [
    ("CREATE", "Create"),
    ("CANCEL", "Cancel"),
]
