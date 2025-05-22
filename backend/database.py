from pymongo import MongoClient

uri = "mongodb://localhost:27017/" 
client = MongoClient(uri)

db = client["ocr_prompts"]
collection = db["prompts"]
    
# Check if collection exists, if not create it
if "prompts" not in db.list_collection_names():
    db.create_collection("prompts")

def add_default_prompt(prompt):
    if collection.count_documents({"default_type": "pdf"}) == 0:
        collection.insert_one({"default_type": "pdf", "default_prompt": prompt})

def update_id():
    try:
        # Get count of documents with file_name
        total_docs = collection.count_documents({"file_name": {"$exists": True}})
        
        # Get all documents with file_name in order
        documents = list(collection.find(
            {"file_name": {"$exists": True}},
            sort=[("uploaded_at", 1)]
        ))
        
        # Update document IDs to match the count
        for i, doc in enumerate(documents, 1):
            if i <= total_docs:
                collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"document_id": i}}
                )
            else:
                # Remove document_id if it exceeds the count
                collection.update_one(
                    {"_id": doc["_id"]},
                    {"$unset": {"document_id": ""}}
                )
    except Exception as e:
        print(f"Error updating document IDs:{str(e)}")
    