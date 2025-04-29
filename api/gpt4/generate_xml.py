import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from lxml import etree

from api.gpt4.utils import obtener_ruta_schema_transferencia


logger = logging.getLogger("bank_services")


def generar_xml_pain001(transferencia, payment_id):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)

    # Crear el root del XML
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")

    # Cabecera del grupo
    grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(grp_hdr, "CreDtTm").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
    ET.SubElement(grp_hdr, "CtrlSum").text = str(transferencia.instructed_amount)
    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    ET.SubElement(initg_pty, "Nm").text = transferencia.debtor.name

    # Información del pago
    pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
    ET.SubElement(pmt_inf, "PmtInfId").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
    ET.SubElement(pmt_inf, "BtchBookg").text = "false"
    ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
    ET.SubElement(pmt_inf, "CtrlSum").text = str(transferencia.instructed_amount)

    # Información del tipo de pago
    pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
    svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
    ET.SubElement(svc_lvl, "Cd").text = (
        transferencia.payment_type_information.service_level_code if transferencia.payment_type_information else "INST"
    )
    if transferencia.payment_type_information and transferencia.payment_type_information.local_instrument_code:
        lcl_instrm = ET.SubElement(pmt_tp_inf, "LclInstrm")
        ET.SubElement(lcl_instrm, "Cd").text = transferencia.payment_type_information.local_instrument_code
    if transferencia.payment_type_information and transferencia.payment_type_information.category_purpose_code:
        ctgy_purp = ET.SubElement(pmt_tp_inf, "CtgyPurp")
        ET.SubElement(ctgy_purp, "Cd").text = transferencia.payment_type_information.category_purpose_code

    # Datos del deudor
    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = transferencia.debtor.name
    dbtr_pstl_adr = ET.SubElement(dbtr, "PstlAdr")
    ET.SubElement(dbtr_pstl_adr, "StrtNm").text = transferencia.debtor.postal_address_street
    ET.SubElement(dbtr_pstl_adr, "TwnNm").text = transferencia.debtor.postal_address_city
    ET.SubElement(dbtr_pstl_adr, "Ctry").text = transferencia.debtor.postal_address_country

    dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
    dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
    ET.SubElement(dbtr_acct_id, "IBAN").text = transferencia.debtor_account.iban

    # Información de la transferencia individual
    cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
    pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
    ET.SubElement(pmt_id, "EndToEndId").text = str(transferencia.payment_identification.end_to_end_id)  # Convertir UUID a cadena
    ET.SubElement(pmt_id, "InstrId").text = str(transferencia.payment_identification.instruction_id)
    
    amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
    ET.SubElement(amt, "InstdAmt", Ccy=transferencia.currency).text = str(transferencia.instructed_amount)

    # Datos del acreedor
    cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
    ET.SubElement(cdtr, "Nm").text = transferencia.creditor.name
    cdtr_pstl_adr = ET.SubElement(cdtr, "PstlAdr")
    ET.SubElement(cdtr_pstl_adr, "StrtNm").text = transferencia.creditor.postal_address_street
    ET.SubElement(cdtr_pstl_adr, "TwnNm").text = transferencia.creditor.postal_address_city
    ET.SubElement(cdtr_pstl_adr, "Ctry").text = transferencia.creditor.postal_address_country

    cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
    cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
    ET.SubElement(cdtr_acct_id, "IBAN").text = transferencia.creditor_account.iban

    # Agente del acreedor
    cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
    fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
    ET.SubElement(fin_instn_id, "BIC").text = transferencia.creditor_agent.bic

    # Información de la remesa
    rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
    if transferencia.remittance_information_structured:
        ET.SubElement(rmt_inf, "Strd").text = transferencia.remittance_information_structured
    if transferencia.remittance_information_unstructured:
        ET.SubElement(rmt_inf, "Ustrd").text = transferencia.remittance_information_unstructured

    # Guardar XML
    xml_filename = f"pain001_{payment_id}.xml"
    xml_path = os.path.join(carpeta_transferencia, xml_filename)
    ET.ElementTree(root).write(xml_path, encoding='utf-8', xml_declaration=True)

    logger.info(f"XML pain.001 generado en {xml_path}")
    return xml_path


def validar_xml_pain001(xml_path):
    """
    Verifica que el XML generado contenga EndToEndId e InstrId.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    ns = {'ns': "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"}
    e2e = root.find('.//ns:EndToEndId', ns)
    instr = root.find('.//ns:InstrId', ns)

    if e2e is None or not e2e.text.strip():
        raise ValueError("El XML no contiene un EndToEndId válido.")
    if instr is None or not instr.text.strip():
        raise ValueError("El XML no contiene un InstructionId válido.")


def validar_xml_con_xsd(xml_path, xsd_path="schemas/xsd/pain.001.001.03.xsd"):
    """
    Valida el archivo XML `pain.001` contra el esquema XSD.
    """
    with open(xsd_path, 'rb') as f:
        schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

    with open(xml_path, 'rb') as f:
        xml_doc = etree.parse(f)

    if not schema.validate(xml_doc):
        errors = schema.error_log
        raise ValueError(f"El XML no es válido según el XSD: {errors}")