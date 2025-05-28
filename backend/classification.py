import os
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from .database import collection


os.environ["GOOGLE_API_KEY"] = "AIzaSyCWpx-nHbCHSm2DZK_KUpJk4cFC4RrLCwc"

def get_gemini_model():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")


def classify_invoice(invoice_json: dict, model) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a document classifier for SAP systems. Follow these steps in order to classify the document:

1. First, check if it's an outgoing_payment:
   - check the payment_details.net_amount if it is less than 2000 than it is outgoing payments
   - Look for payment-related keywords like 'payment', 'voucher', 'receipt'
   - If both conditions are met, classify as 'outgoing_payment'

2. If not an outgoing_payment, check if it's an ap_invoice_with_lc:
   - Look for LC (Letter of Credit) references in:
     * payment mode
     * particulars/description
     * vendor details
     * lc_no
   - if invoice_details.lc_no is preset it is ap_invoice_with_lc  
   - If LC is found, classify as 'ap_invoice_with_lc'

3. If neither of the above, classify as 'ap_invoice':
   - This is the default for standard vendor invoices
   - No special conditions needed

Important:
- Follow the order: outgoing_payment → ap_invoice_with_lc → ap_invoice
- Return ONLY one of these labels: outgoing_payment, ap_invoice_with_lc, or ap_invoice
- Do not include any explanations or additional text
"""),
        ("user", "Here is the invoice data:\n{invoice_json}")
    ])

    chain = prompt | model

    try:
        response = chain.invoke({
            "invoice_json": json.dumps(invoice_json, indent=2)
        })
        return response.content.strip()
    except Exception as e:
        return f"Classification failed: {type(e).__name__} - {e}"
extracted_json_data =  collection.find_one(sort = [("_id", -1)], projection = {"extracted_detail": 1, "_id":0})
extracted_file_from =  collection.find_one(sort = [("_id", -1)], projection = {"file_name": 1, "_id":0})
invoice_json_data = f"""{extracted_json_data}"""
# invoice_json_data = """{\n  "InvoiceNo": "12081/82/06/0000237456",\n  "SellerPANVATNo": "300325694",\n  "SellerName": "Ncell Axiata Limited",\n  "SellerAddress": "Lalitpur District, Lalitpur Metropolitan City, Ward No. 4, Ekantakuna",\n  "FromNcell": "9005",\n  "FromOtherOperators": "+977 9809005000",\n  "Facsimile": "+977 9805554442",\n  "ClientName": "Sarbottam Steels Ltd.",\n  "ClientAddress": "NEPAL Bagmati Kathmandu Subinagar 35",\n  "ClientPANVATNo": "605976829",\n  "PaymentTerms": "Cash/Cheque/Credit/Others",\n  "PhoneNo": "9802266500",\n  "DateBSAD": "1 Poush 2081 00:07:19",\n  "DateAD": "16-12-2024 00:07:19",\n  "PrintDate": "19/12/2024 10:47:57",\n  "TranslationNo": "173383395370",\n  "ResourceCode": "",\n  "AccountNo": "3.112208860013",\n  "MobileNo": "9802266500",\n  "PaymentType": "Invoice",\n  "PrintedBy": "",\n  "CollectionItem": "HSC:NA",\n  "CashRecharge": "511.89",\n  "TotalChargesBeforeTax": "511.89",\n  "InvoiceAmount": "",\n  "TSC": "51.19",\n  "InvoiceStatementNo": "OT: 11.26",\n  "PaymentMode": "Bank",\n  "VAT": "74.66",\n  "ChequeVoucherNo": "",\n  "PenaltyAdjustment": "",\n  "NameOfBank": "",\n  "CreditAdjustment": "",\n  "RebateAdjustment": "",\n  "SubmittedAmount": "649.00",\n  "TotalReceived": "649.00",\n  "ReceivedAmtInWords": "Rs Six Hundred and Forty Nine rupee and Zero paisas",\n  "Note": "Payments received by cheques are subject to the collection by the concerned bank."\n}"""

invoice_data = json.loads(invoice_json_data)

model = get_gemini_model()
classification_result = classify_invoice(invoice_data, model)

# print("📄 Document Type:", classification_result)
