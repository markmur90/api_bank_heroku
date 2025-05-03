import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.error_response import ErrorResponse  # noqa: E501
from openapi_server.models.sepa_credit_transfer_details_response import SepaCreditTransferDetailsResponse  # noqa: E501
from openapi_server import util


def payment_id_get(payment_id, correlation_id=None):  # noqa: E501
    """Retrieve the Sepa Credit Transfer details

    Retrieve the details of a previously initiated Sepa Credit Transfer. # noqa: E501

    :param payment_id: Payment Id of Sepa Credit Transfer
    :type payment_id: str
    :type payment_id: str
    :param correlation_id: Free form key controlled by the caller e.g. uuid
    :type correlation_id: str

    :rtype: Union[SepaCreditTransferDetailsResponse, Tuple[SepaCreditTransferDetailsResponse, int], Tuple[SepaCreditTransferDetailsResponse, int, Dict[str, str]]
    """
    return 'do some magic!'
