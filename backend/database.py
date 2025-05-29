from pymongo import MongoClient

uri = "mongodb://localhost:27017/" 
client = MongoClient(uri)

db = client["ocr_prompts"]
collection = db["prompts"]
    
if "prompts" not in db.list_collection_names():
    db.create_collection("prompts")

def add_default_prompt(prompt):
    if collection.count_documents({"default_type": "pdf"}) == 0:
        collection.insert_one({"default_type": "pdf", "default_prompt": prompt})

    