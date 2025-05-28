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
        ("system", """You are a document classifier for SAP systems. Based on the invoice JSON data, classify the document into one of the following types:
- ap_invoice
- ap_invoice_with_lc
- outgoing_payment

Your classification should depend on the nature of the document:
- 'ap_invoice' is a standard vendor invoice
- 'ap_invoice_with_lc' includes reference to LC (Letter of Credit) in payment mode, particulars, or vendor behavior
- 'outgoing_payment' represents documents that relate directly to a payment, like a payment voucher

Respond with only one of the labels: ap_invoice, ap_invoice_with_lc, or outgoing_payment.
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

invoice_data = json.loads(invoice_json_data)

model = get_gemini_model()
classification_result = classify_invoice(invoice_data, model)

print("📄 Document Type:", classification_result)
