import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.error_response import ErrorResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_response import SepaCreditTransferResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_update_sca_request import SepaCreditTransferUpdateScaRequest  # noqa: E501
from openapi_server import util


def payment_id_patch(payment_id, idempotency_id, otp, body, correlation_id=None):  # noqa: E501
    """Second factor retry for Sepa Credit Transfer

    User can retry the second factor if it&#39;s failed, The new once&#39;s will be initiated after deleting the existing once&#39;s. # noqa: E501

    :param payment_id: Payment Id of Sepa Credit Transfer
    :type payment_id: str
    :type payment_id: str
    :param idempotency_id: Unique id of the service call. Must be present during retries to avoid multiple processing of the same request
    :type idempotency_id: str
    :type idempotency_id: str
    :param otp: One time password required for second factor update, in case of push tan use &#39;PUSHTAN&#39;. in case of photo tan please generate otp by using transaction authorisation APIs. there you must use requestType corresponds to the action. for create action it must be &#39;SEPA_TRANSFER_GRANT&#39; and for cancel &#39;SEPA_TRANSFER_CANCELLATION&#39;.
    :type otp: str
    :param sepa_credit_transfer_update_sca_request: 
    :type sepa_credit_transfer_update_sca_request: dict | bytes
    :param correlation_id: Free form key controlled by the caller e.g. uuid
    :type correlation_id: str

    :rtype: Union[SepaCreditTransferResponse, Tuple[SepaCreditTransferResponse, int], Tuple[SepaCreditTransferResponse, int, Dict[str, str]]
    """
    sepa_credit_transfer_update_sca_request = body
    if connexion.request.is_json:
        sepa_credit_transfer_update_sca_request = SepaCreditTransferUpdateScaRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
