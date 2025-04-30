import unittest

from flask import json

from openapi_server.models.error_response import ErrorResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_details_response import SepaCreditTransferDetailsResponse  # noqa: E501
from openapi_server.test import BaseTestCase


class TestGetSepaCreditTransferDetailsController(BaseTestCase):
    """GetSepaCreditTransferDetailsController integration test stubs"""

    def test_payment_id_get(self):
        """Test case for payment_id_get

        Retrieve the Sepa Credit Transfer details
        """
        headers = { 
            'Accept': 'application/json',
            'correlation_id': 'correlation_id_example',
            'Authorization': 'Bearer special-key',
            'Authorization': 'Bearer special-key',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{payment_id}'.format(payment_id='payment_id_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
