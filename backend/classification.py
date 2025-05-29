import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from .database import collection


os.environ["GOOGLE_API_KEY"] = "AIzaSyCWpx-nHbCHSm2DZK_KUpJk4cFC4RrLCwc"

total_uploads = collection.count_documents({"file_name": {"$exists":True}})
raw_json = collection.find_one({"uid": total_uploads},{"extracted_details":1, "_id": 0 })
raw_json_string = json.dumps(raw_json)

def get_gemini_model():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")

def classify_invoice(invoice_json: dict, model) -> str:
    # First, check the net_amount condition directly in Python
    try:
        net_amount = invoice_json.get("payment_details", {}).get("net_amount")
        if net_amount is not None and net_amount < 2000:
            return "outgoing_payment"
    except (TypeError, ValueError):
        # Handle cases where net_amount is not a valid number
        pass

    # If the net_amount condition is not met, use the model for classification
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a document classifier for SAP systems. Based on the invoice JSON data, classify the document into one of the following types:
- ap_invoice
- ap_invoice_with_lc

Your classification should depend on the nature of the document:
- 'ap_invoice' is a standard vendor invoice
- 'ap_invoice_with_lc' includes reference to LC (Letter of Credit) in payment mode, particulars, or vendor behavior (if invoice_details.lc_no is preset it is ap_invoice_with_lc)

Respond with only one of the labels: ap_invoice or ap_invoice_with_lc.
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
    
# raw_json_string = collection.find_one(
#     filter={},  
#     sort=[("uid", -1)],  
#     projection={"extracted_details": 1, "_id": 0}  # Only get extracted_details field
# )


extracted_file_from = collection.find_one(
    filter={},  # No filter, get all documents
    sort=[("uid", -1)],  # Sort by _id in descending order
    projection={"file_name": 1, "_id": 0}  # Only get extracted_details field
)

# print("Latest document extracted details:")
# print(json.dumps(raw_json_string, indent=2))

# cleaned_json_string = json.dumps(raw_json_string).replace("'\n' +    '", "").replace("'\n'", "").replace("'''", "").replace("+","").replace("\n","").replace("\'","").strip()
# cleaned_json_string = cleaned_json_string[1:-1]

# Since raw_json_string is already a dictionary from MongoDB, we can use it directly
# extracted_data = raw_json_string.get('extracted_details')

####################
## FROM THE COLAB ##
####################
# Find the start and end of the JSON object
json_start = raw_json_string.find('{')
json_end = raw_json_string.rfind('}')

if json_start != -1 and json_end != -1:
    # Extract the JSON substring
    json_substring = raw_json_string[json_start : json_end + 1]

    # Parse the JSON substring
    try:
        invoice_data_dict = json.loads(json_substring)
        print("JSON parsed successfully!")


    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
else:
    print("Could not find a valid JSON object in the string.")

model = get_gemini_model()


classification_result = classify_invoice(invoice_data_dict, model)

# print("📄 Document Type:", classification_result)
# print(type(raw_json))