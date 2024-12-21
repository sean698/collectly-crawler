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
import base64
class TreasureFinderPipeline:
    is_initialized = False
    
    def __init__(self):
        self.items = []
        if not TreasureFinderPipeline.is_initialized:
            self.initialize_firebase()
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

    def _format_price(self, price):
        if not price:
            return None
        try:
            return int(''.join(c for c in price if c.isdigit())) or 0
        except:
            return 0

    def process_item(self, item, spider):
        try:
            item = self._format_location(item)
            
            if 'price' in item:
                item['price'] = self._format_price(item['price'])
            
            url = item.get('url')
            if not url:
                raise ValueError("Item must have a URL")
                
            db = firestore.client()
            collection_ref = db.collection('rental_listings')
            
            doc_id = f"{item.get('source')}_{base64.urlsafe_b64encode(url.encode()).decode()}"
            listing_ref = collection_ref.document(doc_id)
            
            data = dict(item)
            
            try:
                listing_ref.update(data)
                print(f"Updated existing listing: {item['source']}")
            except:
                data['createdAt'] = firestore.SERVER_TIMESTAMP
                data['expiresAt'] = datetime.now() + timedelta(days=7)
                listing_ref.set(data)
                print(f"Created new listing: {item['source']}")
            
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
            print(f"Failed item: {item}")
        
        return item

    