import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from api.sct.models import SepaCreditTransferRequest
from sepa_proyecto_completo.sepa_transferencias.helpers import obtener_ruta_schema_transferencia

logger = logging.getLogger("bank_services")


def generate_sepa_xml(transfers: SepaCreditTransferRequest) -> str:

    try:
        # Create the root element of the XML
        root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
        cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")
        
        # Header group
        grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
        ET.SubElement(grp_hdr, "MsgId").text = str(transfers.idempotency_key)
        ET.SubElement(grp_hdr, "CreDtTm").text = datetime.utcnow().isoformat()
        ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
        ET.SubElement(grp_hdr, "CtrlSum").text = str(transfers.instructed_amount)
        initg_pty = ET.SubElement(grp_hdr, "InitgPty")
        ET.SubElement(initg_pty, "Nm").text = transfers.debtor_name
        
        # Payment information
        pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
        ET.SubElement(pmt_inf, "PmtInfId").text = str(transfers.payment_id)
        ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
        ET.SubElement(pmt_inf, "BtchBookg").text = "false"
        ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
        ET.SubElement(pmt_inf, "CtrlSum").text = str(transfers.instructed_amount)
        
        # Configuration for Instant SEPA Credit Transfer
        pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
        # ET.SubElement(pmt_tp_inf, "InstrPrty").text = "HIGH"
        svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
        ET.SubElement(svc_lvl, "Cd").text = "SEPA"
        
        # Debtor
        dbtr = ET.SubElement(pmt_inf, "Dbtr")
        ET.SubElement(dbtr, "Nm").text = transfers.debtor_name
        
        # Debtor address
        dbtr_pstl_adr = ET.SubElement(dbtr, "PstlAdr")
        ET.SubElement(dbtr_pstl_adr, "StrtNm").text = transfers.debtor_adress_street_and_house_number
        ET.SubElement(dbtr_pstl_adr, "TwnNm").text = transfers.debtor_adress_zip_code_and_city
        ET.SubElement(dbtr_pstl_adr, "Ctry").text = transfers.debtor_adress_country
        
        # Debtor account
        dbtr_pty = ET.SubElement(pmt_inf, "DbtrAcct")
        dbtr_pty_id = ET.SubElement(dbtr_pty, "Id")
        ET.SubElement(dbtr_pty_id, "IBAN").text = transfers.debtor_account_iban
        
        # Debtor agent
        dbtr_agt = ET.SubElement(pmt_inf, "DbtrAgt")
        dbtr_agt_fin_instn_id = ET.SubElement(dbtr_agt, "FinInstnId")
        ET.SubElement(dbtr_agt_fin_instn_id, "BIC").text = transfers.debtor_account_bic
        
        # Transaction information
        cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
        pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
        ET.SubElement(pmt_id, "EndToEndId").text = str(transfers.payment_identification_end_to_end_id)
        
        # Amount
        amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
        ET.SubElement(amt, "InstdAmt", Ccy=transfers.instructed_currency).text = str(transfers.instructed_amount)
        
        # Creditor
        cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
        ET.SubElement(cdtr, "Nm").text = transfers.creditor_name
        
        # Creditor address
        cdtr_pstl_adr = ET.SubElement(cdtr, "PstlAdr")
        ET.SubElement(cdtr_pstl_adr, "StrtNm").text = transfers.creditor_adress_street_and_house_number
        ET.SubElement(cdtr_pstl_adr, "TwnNm").text = transfers.creditor_adress_zip_code_and_city
        ET.SubElement(cdtr_pstl_adr, "Ctry").text = transfers.creditor_adress_country
        
        # Creditor account
        cdtr_pty = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
        cdtr_pty_id = ET.SubElement(cdtr_pty, "Id")
        ET.SubElement(cdtr_pty_id, "IBAN").text = transfers.creditor_account_iban
        ET.SubElement(cdtr_pty, "Ccy").text = transfers.creditor_account_currency
        
        # Creditor agent
        cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
        cdtr_agt_fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
        if transfers.creditor_agent_financial_institution_id:
            ET.SubElement(cdtr_agt_fin_instn_id, "Othr").text = transfers.creditor_agent_financial_institution_id
        ET.SubElement(cdtr_agt_fin_instn_id, "BIC").text = transfers.creditor_account_bic
        
        # Additional information
        rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
        if transfers.remittance_information_structured:
            ET.SubElement(rmt_inf, "Strd").text = transfers.remittance_information_structured
        if transfers.remittance_information_unstructured:
            ET.SubElement(rmt_inf, "Ustrd").text = transfers.remittance_information_unstructured
        
        # Convert the XML tree to a string
        xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
        
        logger.info(f"Generated SEPA XML for transfer with payment_id {transfers.payment_id}")
        return xml_string
        
    except Exception as e:
        logger.error(f"Error generating XML file: {str(e)}", exc_info=True)
        raise

def generar_xml_pain001(transferencia, payment_id):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
    root = ET.Element("Document")
    CstmrCdtTrfInitn = ET.SubElement(root, "CstmrCdtTrfInitn")
    PmtInf = ET.SubElement(CstmrCdtTrfInitn, "PmtInf")
    ET.SubElement(PmtInf, "PmtInfId").text = transferencia.payment_identification.instruction_id
    ET.SubElement(PmtInf, "ReqdExctnDt").text = transferencia.requested_execution_date.strftime("%Y-%m-%d")
    Cdtr = ET.SubElement(PmtInf, "Cdtr")
    ET.SubElement(Cdtr, "Nm").text = transferencia.creditor.creditor_name
    CdtrAcct = ET.SubElement(PmtInf, "CdtrAcct")
    ET.SubElement(CdtrAcct, "IBAN").text = transferencia.creditor_account.iban
    Dbtr = ET.SubElement(PmtInf, "Dbtr")
    ET.SubElement(Dbtr, "Nm").text = transferencia.debtor.debtor_name
    DbtrAcct = ET.SubElement(PmtInf, "DbtrAcct")
    ET.SubElement(DbtrAcct, "IBAN").text = transferencia.debtor_account.iban
    Amt = ET.SubElement(PmtInf, "Amt")
    ET.SubElement(Amt, "InstdAmt", Ccy=transferencia.instructed_amount.currency).text = str(transferencia.instructed_amount.amount)
    xml_filename = f"pain001_{payment_id}.xml"
    xml_path = os.path.join(carpeta_transferencia, xml_filename)
    ET.ElementTree(root).write(xml_path, encoding='utf-8', xml_declaration=True)
    return xml_path