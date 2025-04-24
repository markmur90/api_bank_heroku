import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from .models import SepaCreditTransferRequest
from .helpers import obtener_ruta_schema_transferencia

logger = logging.getLogger("bank_services")

def generar_xml_pain001(transferencia, payment_id):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")

    grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = transferencia.payment_id
    ET.SubElement(grp_hdr, "CreDtTm").text = datetime.utcnow().isoformat()
    ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
    ET.SubElement(grp_hdr, "CtrlSum").text = str(transferencia.instructed_amount.amount)
    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    ET.SubElement(initg_pty, "Nm").text = transferencia.debtor.debtor_name

    pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
    ET.SubElement(pmt_inf, "PmtInfId").text = transferencia.payment_id
    ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
    ET.SubElement(pmt_inf, "BtchBookg").text = "false"
    ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
    ET.SubElement(pmt_inf, "CtrlSum").text = str(transferencia.instructed_amount.amount)

    pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
    svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
    ET.SubElement(svc_lvl, "Cd").text = "SEPA"

    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = transferencia.debtor.debtor_name
    dbtr_pstl_adr = ET.SubElement(dbtr, "PstlAdr")
    ET.SubElement(dbtr_pstl_adr, "StrtNm").text = transferencia.debtor.postal_address.street_and_house_number
    ET.SubElement(dbtr_pstl_adr, "TwnNm").text = transferencia.debtor.postal_address.zip_code_and_city
    ET.SubElement(dbtr_pstl_adr, "Ctry").text = transferencia.debtor.postal_address.country

    dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
    dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
    ET.SubElement(dbtr_acct_id, "IBAN").text = transferencia.debtor_account.iban

    cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
    pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
    ET.SubElement(pmt_id, "EndToEndId").text = transferencia.payment_identification.end_to_end_id

    amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
    ET.SubElement(amt, "InstdAmt", Ccy=transferencia.instructed_amount.currency).text = str(transferencia.instructed_amount.amount)

    cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
    ET.SubElement(cdtr, "Nm").text = transferencia.creditor.creditor_name
    cdtr_pstl_adr = ET.SubElement(cdtr, "PstlAdr")
    ET.SubElement(cdtr_pstl_adr, "StrtNm").text = transferencia.creditor.postal_address.street_and_house_number
    ET.SubElement(cdtr_pstl_adr, "TwnNm").text = transferencia.creditor.postal_address.zip_code_and_city
    ET.SubElement(cdtr_pstl_adr, "Ctry").text = transferencia.creditor.postal_address.country

    cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
    cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
    ET.SubElement(cdtr_acct_id, "IBAN").text = transferencia.creditor_account.iban
    ET.SubElement(cdtr_acct, "Ccy").text = transferencia.creditor_account.currency

    cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
    cdtr_agt_fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
    ET.SubElement(cdtr_agt_fin_instn_id, "BIC").text = transferencia.creditor_agent.financial_institution_id

    rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
    if transferencia.remittance_information_structured:
        ET.SubElement(rmt_inf, "Strd").text = transferencia.remittance_information_structured
    if transferencia.remittance_information_unstructured:
        ET.SubElement(rmt_inf, "Ustrd").text = transferencia.remittance_information_unstructured

    xml_filename = f"pain001_{payment_id}.xml"
    xml_path = os.path.join(carpeta_transferencia, xml_filename)
    ET.ElementTree(root).write(xml_path, encoding='utf-8', xml_declaration=True)
    return xml_path