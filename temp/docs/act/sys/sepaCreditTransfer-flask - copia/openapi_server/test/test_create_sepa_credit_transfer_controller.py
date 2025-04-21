import unittest

from flask import json

from openapi_server.models.error_response import ErrorResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_request import SepaCreditTransferRequest  # noqa: E501
from openapi_server.models.sepa_credit_transfer_response import SepaCreditTransferResponse  # noqa: E501
from openapi_server.test import BaseTestCase


class TestCreateSEPACreditTransferController(BaseTestCase):
    """CreateSEPACreditTransferController integration test stubs"""

    def test_root_post(self):
        """Test case for root_post

        Initiates a SEPA Credit Transfer
        """
        sepa_credit_transfer_request = {"debtorAccount":{"iban":"iban","currency":"EUR"},"paymentIdentification":{"instructionId":"instructionId","endToEndId":"endToEndId"},"requestedExecutionDate":"2000-01-23","debtor":{"debtorName":"debtorName","debtorPostalAddress":{"country":"DE","addressLine":{"zipCodeAndCity":"zipCodeAndCity","streetAndHouseNumber":"streetAndHouseNumber"}}},"creditorAgent":{"financialInstitutionId":"financialInstitutionId"},"remittanceInformationStructured":"remittanceInformationStructured","purposeCode":"purposeCode","creditorAccount":{"iban":"iban","currency":"EUR"},"instructedAmount":{"amount":58.13,"currency":"EUR"},"creditor":{"creditorName":"creditorName","creditorPostalAddress":{"country":"DE","addressLine":{"zipCodeAndCity":"zipCodeAndCity","streetAndHouseNumber":"streetAndHouseNumber"}}},"remittanceInformationUnstructured":"remittanceInformationUnstructured"}
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
            '/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/',
            method='POST',
            headers=headers,
            data=json.dumps(sepa_credit_transfer_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
