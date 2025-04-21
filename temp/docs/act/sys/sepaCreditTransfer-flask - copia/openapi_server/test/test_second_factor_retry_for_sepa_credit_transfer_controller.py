import unittest

from flask import json

from openapi_server.models.error_response import ErrorResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_response import SepaCreditTransferResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_update_sca_request import SepaCreditTransferUpdateScaRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestSecondFactorRetryForSepaCreditTransferController(BaseTestCase):
    """SecondFactorRetryForSepaCreditTransferController integration test stubs"""

    def test_payment_id_patch(self):
        """Test case for payment_id_patch

        Second factor retry for Sepa Credit Transfer
        """
        sepa_credit_transfer_update_sca_request = {"action":"CREATE","authId":"232ed5b7-fc70-4c67-98bb-bf95b3300001"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'idempotency_id': 'idempotency_id_example',
            'otp': 'otp_example',
            'correlation_id': 'correlation_id_example',
            'Authorization': 'Bearer special-key',
            'Authorization': 'Bearer special-key',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{payment_id}'.format(payment_id='payment_id_example'),
            method='PATCH',
            headers=headers,
            data=json.dumps(sepa_credit_transfer_update_sca_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
