# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import firebase_admin
import os
import json
from firebase_admin import credentials, firestore

class TreasureFinderPipeline:
    def __init__(self):
       self.items = []
       self.initialize_firebase()
       
    def initialize_firebase(self):
       try:
        #    cred = credentials.Certificate('C:/Users/shiyu/Downloads/treasure-finder-62cd0-firebase-adminsdk-jvhgm-584391c9d5.json')
           private_key = json.loads(os.environ.get('firebasePrivateKey'))
           cred = credentials.Certificate(private_key)
           try:
               firebase_admin.initialize_app(cred)
           except ValueError:
               pass
           print("Firebase initialized successfully")
       except Exception as e:
           print(f"Firebase initialization error: {e}")
    def process_item(self, item, spider):
        try:
            db = firestore.client()
            collection_ref = db.collection('rent_listings')
            source_doc = 'vanpeople' if item.get('source') == 'vanpeople' else 'craigslist'
            listing_ref = collection_ref.document(source_doc).collection('listings').document()
            listing_ref.set(dict(item))
            print(f"Successfully saved item to rent_listings/{source_doc}/listings: {item}")
            
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
            print(f"Failed item: {item}")
        
        return item
    