import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.error_response import ErrorResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_request import SepaCreditTransferRequest  # noqa: E501
from openapi_server.models.sepa_credit_transfer_response import SepaCreditTransferResponse  # noqa: E501
from openapi_server import util


def root_post(idempotency_id, otp, body, correlation_id=None):  # noqa: E501
    """Initiates a SEPA Credit Transfer

    This API is for creating a Sepa Credit Transfer # noqa: E501

    :param idempotency_id: Unique id of the service call. Must be present during retries to avoid multiple processing of the same request
    :type idempotency_id: str
    :type idempotency_id: str
    :param otp: One time password required for SCT creation, you can use photo tan or push tan. In case of push tan pass otp as &#39;PUSHTAN&#39;. in case of photo tan please generate otp by using transaction authorisation APIs. there you must use requestType as &#39;SEPA_TRANSFER_GRANT&#39;.
    :type otp: str
    :param sepa_credit_transfer_request: 
    :type sepa_credit_transfer_request: dict | bytes
    :param correlation_id: Free form key controlled by the caller e.g. uuid
    :type correlation_id: str

    :rtype: Union[SepaCreditTransferResponse, Tuple[SepaCreditTransferResponse, int], Tuple[SepaCreditTransferResponse, int, Dict[str, str]]
    """
    sepa_credit_transfer_request = body
    if connexion.request.is_json:
        sepa_credit_transfer_request = SepaCreditTransferRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
