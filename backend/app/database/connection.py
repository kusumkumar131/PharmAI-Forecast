from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from app.config import settings

logger = logging.getLogger("pharmacy_app")
logging.basicConfig(level=logging.INFO)

class DatabaseManager:
    client: MongoClient = None
    db = None

    def connect(self):
        try:
            masked_url = settings.MONGODB_URL
            if "@" in masked_url and "://" in masked_url:
                prefix, rest = masked_url.split("://", 1)
                creds, host = rest.split("@", 1)
                masked_url = f"{prefix}://***:***@{host}"
            logger.info(f"Connecting to MongoDB at {masked_url}...")
            self.client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
            # Verify server is responsive
            self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            logger.info(f"Successfully connected to MongoDB database: '{settings.DATABASE_NAME}'")
            self.setup_indexes()
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def setup_indexes(self):
        """Create indexes for performance and data integrity across collections."""
        try:
            # Users
            self.db.users.create_index([("email", ASCENDING)], unique=True)

            # Medicines
            self.db.medicines.create_index([("medicine_id", ASCENDING)], unique=True)
            self.db.medicines.create_index([("category", ASCENDING)])
            self.db.medicines.create_index([("medicine_name", ASCENDING)])

            # Batches
            self.db.batches.create_index([("batch_id", ASCENDING)], unique=True)
            self.db.batches.create_index([("medicine_id", ASCENDING), ("expiry_date", ASCENDING)])
            self.db.batches.create_index([("expiry_date", ASCENDING)])

            # Sales
            self.db.sales.create_index([("transaction_id", ASCENDING)], unique=True)
            self.db.sales.create_index([("medicine_id", ASCENDING)])
            self.db.sales.create_index([("sale_date", DESCENDING)])

            # Purchases
            self.db.purchases.create_index([("purchase_id", ASCENDING)], unique=True)
            self.db.purchases.create_index([("medicine_id", ASCENDING)])

            # Forecasts
            self.db.forecasts.create_index([("forecast_id", ASCENDING)], unique=True)
            self.db.forecasts.create_index([("medicine_id", ASCENDING), ("forecast_date", ASCENDING)])

            # Expiry alerts
            self.db.expiry_alerts.create_index([("alert_id", ASCENDING)], unique=True)
            self.db.expiry_alerts.create_index([("batch_id", ASCENDING)])
            self.db.expiry_alerts.create_index([("risk_level", ASCENDING)])

            logger.info("MongoDB indexes verified and ensured.")
        except Exception as e:
            logger.warning(f"Could not build indexes during initialization: {e}")

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

db_manager = DatabaseManager()

def get_db():
    if db_manager.db is None:
        db_manager.connect()
    return db_manager.db
