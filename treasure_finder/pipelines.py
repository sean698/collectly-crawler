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
from treasure_finder.constants import LOCATION_MAP
from datetime import datetime, timedelta

class TreasureFinderPipeline:
    is_initialized = False
    
    def __init__(self):
        self.items = []
        if not TreasureFinderPipeline.is_initialized:
            self.initialize_firebase()
            self.clear_collection()
            TreasureFinderPipeline.is_initialized = True
       
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

    def clear_collection(self):
        try:
            db = firestore.client()
            batch_size = 500
            
            sources = db.collection('rental_listings').list_documents()
            
            for source in sources:
                listings = source.collection('listings').limit(batch_size).stream()
                
                batch = db.batch()
                count = 0
                
                for listing in listings:
                    batch.delete(listing.reference)
                    count += 1
                    
                    if count >= batch_size:
                        batch.commit()
                        batch = db.batch()
                        count = 0
                
                if count > 0:
                    batch.commit()
                    
                source.delete() 
            print("Successfully cleared rental_listings collection")
        except Exception as e:
            print(f"Error clearing collection: {e}")

    def _format_location(self, item):
        if item.get('source') == 'vanpeople':
            if item.get('location') in LOCATION_MAP:
                item['location'] = LOCATION_MAP[item['location']]
        
        if item.get('source') == 'craigslist':
            location = item.get('location', '')
            for mapped_location in LOCATION_MAP.values():
                if mapped_location.lower() in location.lower():
                    item['location'] = mapped_location
                    break
            
        return item

    def process_item(self, item, spider):
        try:
            item = self._format_location(item)

            db = firestore.client()
            collection_ref = db.collection('rental_listings')
            source_doc = item.get('source')
            listing_ref = collection_ref.document(source_doc).collection('listings').document()
            listing_ref.set(dict(item))
            
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
            print(f"Failed item: {item}")
        
        return item
    