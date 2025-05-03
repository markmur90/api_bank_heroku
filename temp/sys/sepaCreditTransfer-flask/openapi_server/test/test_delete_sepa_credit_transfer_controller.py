import unittest

from flask import json

from openapi_server.models.error_response import ErrorResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_response import SepaCreditTransferResponse  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDeleteSepaCreditTransferController(BaseTestCase):
    """DeleteSepaCreditTransferController integration test stubs"""

    def test_payment_id_delete(self):
        """Test case for payment_id_delete

        Cancel the Sepa Credit Transfer
        """
        headers = { 
            'Accept': 'application/json',
            'idempotency_id': 'idempotency_id_example',
            'otp': 'otp_example',
            'correlation_id': 'correlation_id_example',
            'Authorization': 'Bearer special-key',
            'Authorization': 'Bearer special-key',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{payment_id}'.format(payment_id='payment_id_example'),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
