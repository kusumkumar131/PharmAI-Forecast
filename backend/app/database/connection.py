from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
import logging
import time
import urllib.parse
import certifi

from app.config import settings

logger = logging.getLogger("pharmacy_app")
logging.basicConfig(level=logging.INFO)

def mask_mongo_uri(uri: str) -> str:
    """Masks credentials in MongoDB connection string for safe, credential-free logging."""
    if not uri:
        return "<EMPTY_URI>"
    try:
        if "@" in uri and "://" in uri:
            prefix, rest = uri.split("://", 1)
            creds, host = rest.rsplit("@", 1)
            return f"{prefix}://***:***@{host}"
    except Exception:
        pass
    return "<MASKED_URI>"

def sanitize_mongo_uri(uri: str) -> str:
    """
    Ensures username and password in connection URI are properly URL-encoded
    if they contain unescaped special characters.
    """
    if not uri or "://" not in uri:
        return uri
    try:
        prefix, rest = uri.split("://", 1)
        if "@" in rest:
            user_pass, host_part = rest.rsplit("@", 1)
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                user_clean = urllib.parse.quote_plus(urllib.parse.unquote_plus(user))
                password_clean = urllib.parse.quote_plus(urllib.parse.unquote_plus(password))
                return f"{prefix}://{user_clean}:{password_clean}@{host_part}"
    except Exception as e:
        logger.warning(f"URI sanitization warning: {e}")
    return uri

class DatabaseManager:
    client: MongoClient = None
    db = None

    def connect(self, max_retries: int = 3, retry_delay: float = 2.0) -> bool:
        """
        Connects to MongoDB Atlas using verified TLS CA certificate bundle (certifi).
        Implements connection retries, timeouts, and live ping validation.
        """
        raw_url = settings.MONGODB_URL
        if not raw_url:
            logger.error("MONGODB_URL is not set or empty in environment.")
            return False

        sanitized_url = sanitize_mongo_uri(raw_url)
        masked_url = mask_mongo_uri(sanitized_url)

        is_tls = (
            sanitized_url.startswith("mongodb+srv://")
            or "tls=true" in sanitized_url.lower()
            or "ssl=true" in sanitized_url.lower()
        )

        client_kwargs = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 10000,
            "socketTimeoutMS": 45000,
            "retryWrites": True,
            "appname": "PharmAI-Forecast",
        }

        # Configure verified TLS CA certificate file for Atlas
        if is_tls:
            client_kwargs["tls"] = True
            client_kwargs["tlsCAFile"] = certifi.where()

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to MongoDB at {masked_url} (attempt {attempt}/{max_retries})...")
                self.client = MongoClient(sanitized_url, **client_kwargs)

                # Active Ping Test
                ping_res = self.client.admin.command("ping")
                if ping_res.get("ok") != 1:
                    raise ConnectionFailure(f"MongoDB ping returned unexpected response: {ping_res}")

                self.db = self.client[settings.DATABASE_NAME]
                logger.info(f"Successfully connected and verified MongoDB database: '{settings.DATABASE_NAME}'")
                self.setup_indexes()
                return True
            except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as e:
                logger.error(f"MongoDB connection attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error connecting to MongoDB: {e}")
                break

        logger.critical(f"Failed to establish verified MongoDB connection after {max_retries} attempts.")
        self.db = None
        return False

    def is_connected(self) -> bool:
        """Actively checks if database client is alive and responding to ping."""
        if self.client is None or self.db is None:
            return False
        try:
            res = self.client.admin.command("ping")
            return res.get("ok") == 1
        except Exception:
            return False

    def get_database(self):
        """Returns the database handle, reconnecting if needed."""
        if self.db is None or not self.is_connected():
            self.connect(max_retries=1)
        return self.db

    def setup_indexes(self):
        """Create indexes for performance and data integrity across collections."""
        try:
            if self.db is None:
                return

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
        """Gracefully closes MongoDB connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB connection closed gracefully.")
            except Exception as e:
                logger.warning(f"Error closing MongoDB connection: {e}")
            finally:
                self.client = None
                self.db = None

db_manager = DatabaseManager()

def get_db():
    return db_manager.get_database()
