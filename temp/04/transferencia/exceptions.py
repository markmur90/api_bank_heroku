from rest_framework.exceptions import APIException

class SwiftServerError(APIException):
    status_code = 500
    default_detail = "Error in Swift communication."
    default_code = "swift_server_error"

class InvalidTransactionData(APIException):
    status_code = 400
    default_detail = "Invalid transaction data."
    default_code = "invalid_transaction"
