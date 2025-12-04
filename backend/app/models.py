from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# === DISTRIBUTED SOFTWARE MODEL ===
# Each user has their own SQLite database file
# No user authentication needed - each installation is personal

# === CATEGORY MODEL ===
# This represents spending categories (Food, Transport, etc.)

class Category(Base):
   
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category info
    name = Column(String(50), unique=True, index=True, nullable=False)  # "Food & Dining"
    description = Column(Text, nullable=True)  # "Restaurants, groceries, food delivery"
    color = Column(String(7), default="#007bff")  # Hex color for UI charts: "#FF6B6B"
    icon = Column(String(50), nullable=True)  # Emoji or icon name: "🍽️"
    is_default = Column(Boolean, default=False)  # True for system-created categories
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship: One category can be used by many transactions
    transactions = relationship("Transaction", back_populates="category")
    
    # Relationship: One category can have many learned keywords
    keywords = relationship("CategoryKeyword", back_populates="category", cascade="all, delete-orphan")


# === CATEGORY KEYWORD MODEL ===
# Keyword-based auto-categorization with adaptive learning

class CategoryKeyword(Base):
    
    __tablename__ = "category_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    keyword = Column(String(100), nullable=False, index=True)
    weight = Column(Integer, default=1, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    category = relationship("Category", back_populates="keywords")


# === TRANSACTION MODEL ===
# This is the core model - actual financial transactions

class Transaction(Base):
   
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core transaction data (usually from CSV upload)
    description = Column(String(255), nullable=False)  # "Starbucks Coffee"
    amount = Column(Float, nullable=False)  # -4.50 (negative=expense, positive=income)
    date = Column(DateTime, nullable=False, index=True)  # When it happened
    
    # Links to category (foreign key)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # Can be uncategorized
    # NOTE: No user_id needed in distributed mode - each user has their own database
    
    # Extracted keywords for learning (comma-separated)
    extracted_keywords = Column(String(500), nullable=True)
    
    # CSV upload tracking (for audit trail)
    source_file = Column(String(255), nullable=True)  # "chase_statement_jan2024.csv"
    original_row = Column(Integer, nullable=True)  # Row 15 in the original CSV
    csv_category_name = Column(String(255), nullable=True) # Original CSV category name for user reference and preview use
    
    # Auto-managed timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - SQLAlchemy will automatically handle JOINs
    # NOTE: No user relationship needed in distributed mode
    category = relationship("Category", back_populates="transactions")
    
    # === HELPER PROPERTIES ===
    # These are computed properties, not stored in database
    
    @property
    def absolute_amount(self):
        """Returns positive version of amount (useful for charts)"""
        return abs(self.amount)


# === DEFAULT CATEGORIES DATA ===
# These will be automatically created when we initialize the database

DEFAULT_CATEGORIES = [
    {
        "name": "Food & Dining", 
        "description": "Restaurants, groceries, food delivery", 
        "color": "#FF6B6B",  # Red
        "icon": "🍽️", 
        "is_default": True
    },
    {
        "name": "Transportation", 
        "description": "Gas, public transport, car maintenance", 
        "color": "#4ECDC4",  # Teal
        "icon": "🚗", 
        "is_default": True
    },
    {
        "name": "Shopping", 
        "description": "Clothing, electronics, general shopping", 
        "color": "#45B7D1",  # Blue
        "icon": "🛍️", 
        "is_default": True
    },
    {
        "name": "Entertainment", 
        "description": "Movies, games, subscriptions", 
        "color": "#96CEB4",  # Green
        "icon": "🎬", 
        "is_default": True
    },
    {
        "name": "Bills & Utilities", 
        "description": "Rent, electricity, internet, phone", 
        "color": "#FFEAA7",  # Yellow
        "icon": "📋", 
        "is_default": True
    },
    {
        "name": "Other", 
        "description": "Miscellaneous expenses", 
        "color": "#D3D3D3",  # Gray
        "icon": "📦", 
        "is_default": True
    },
]


# === DEFAULT CATEGORY KEYWORDS ===
# Comprehensive keyword mappings for smart auto-categorization
# Special rules: Positive amounts default to Income category

DEFAULT_KEYWORDS = {
    "Food & Dining": [
        # Major Fast Food Chains
        "starbucks", "mcdonald", "burger king", "wendy", "taco bell", "kfc", "chick-fil-a",
        "chipotle", "subway", "panera", "dunkin", "domino", "pizza hut", "papa john",
        "little caesars", "popeyes", "arby", "sonic", "dairy queen", "five guys",
        # Restaurants
        "restaurant", "cafe", "coffee", "diner", "bistro", "grill", "bar", "pub",
        "olive garden", "applebee", "chili", "outback", "red lobster", "cheesecake factory",
        # Grocery Stores
        "grocery", "supermarket", "whole foods", "trader joe", "safeway", "kroger",
        "publix", "wegmans", "aldi", "food lion", "albertsons", "heb", "giant eagle",
        "winn dixie", "fred meyer", "sprouts", "fresh market",
        # Big Box Stores (food sections)
        "walmart", "target", "costco", "sam club", "bj wholesale",
        # Food Delivery
        "doordash", "uber eats", "grubhub", "postmates", "seamless", "instacart",
        "gopuff", "deliveroo",
        # Generic
        "food", "dining", "meal", "eat", "bakery", "deli", "market", "butcher",
        "produce", "meat", "seafood"
    ],
    
    "Transportation": [
        # Gas Stations
        "shell", "exxon", "chevron", "bp", "mobil", "texaco", "valero", "sunoco",
        "arco", "marathon", "speedway", "wawa", "circle k", "7-eleven", "pilot",
        "flying j", "loves", "gulf", "citgo", "conoco", "phillips 66",
        # Rideshare & Taxi
        "uber", "lyft", "taxi", "cab", "rideshare", "via",
        # Public Transit
        "transit", "metro", "subway", "train", "bus", "rail", "mta", "bart", "cta",
        "septa", "wmata", "mbta", "metrocard", "clipper", "orca", "charlie card",
        # Parking & Tolls
        "parking", "park", "toll", "ezpass", "fastrak", "sunpass", "ipass",
        # Auto Services  
        "gas", "fuel", "auto", "car wash", "oil change", "jiffy lube", "valvoline",
        "pep boys", "autozone", "advance auto", "napa", "mechanic", "tire", "repair",
        "smog", "dmv", "registration", "aaa", "roadside"
    ],
    
    "Shopping": [
        # Online Retailers
        "amazon", "ebay", "etsy", "wayfair", "zappos", "chewy", "overstock",
        "wish", "ali express", "newegg",
        # Payment Processors (when used for shopping/expenses)
        "paypal", "venmo", "square", "stripe",
        # Department Stores
        "macy", "nordstrom", "kohl", "jcpenney", "dillard", "bloomingdale",
        "sears", "belk", "von maur",
        # Discount Stores
        "tjmaxx", "marshalls", "ross", "burlington", "homegoods", "sierra",
        "dollar tree", "dollar general", "family dollar", "big lots",
        # Clothing
        "gap", "old navy", "banana republic", "h&m", "zara", "forever 21",
        "uniqlo", "urban outfitters", "american eagle", "hollister", "abercrombie",
        "victoria secret", "bath body works",
        # Electronics
        "best buy", "apple store", "microsoft store", "gamestop", "micro center",
        # Home Improvement
        "home depot", "lowes", "menards", "ace hardware", "true value",
        # General
        "store", "shop", "shopping", "retail", "mall", "outlet", "market",
        "boutique", "warehouse", "wholesale"
    ],
    
    "Entertainment": [
        # Streaming Services
        "netflix", "hulu", "disney", "disney+", "hbo", "hbo max", "amazon prime",
        "apple tv", "paramount", "peacock", "showtime", "starz", "espn",
        # Music Streaming
        "spotify", "apple music", "pandora", "youtube premium", "tidal", "amazon music",
        # Gaming
        "steam", "playstation", "xbox", "nintendo", "epic games", "blizzard",
        "riot games", "twitch", "gaming",
        # Movies & Events
        "cinema", "theater", "theatre", "movie", "amc", "regal", "cinemark",
        "alamo drafthouse", "imax", "fandango", "moviepass",
        "concert", "ticket", "ticketmaster", "stubhub", "eventbrite", "livenation",
        # Recreation & Fitness
        "gym", "fitness", "planet fitness", "la fitness", "24 hour fitness",
        "equinox", "crunch", "ymca", "yoga", "pilates", "crossfit", "peloton",
        # Hobbies
        "hobby lobby", "michaels", "joann", "books", "barnes noble", "bookstore"
    ],
    
    "Bills & Utilities": [
        # Electric & Gas
        "electric", "electricity", "power", "energy", "pge", "duke energy",
        "con edison", "coned", "southern company", "exelon", "dominion",
        "gas company", "natural gas", "propane",
        # Water & Sewer
        "water", "sewer", "utility", "utilities", "municipal",
        # Trash
        "trash", "garbage", "waste management", "republic services", "recology",
        # Internet & Cable
        "internet", "cable", "comcast", "xfinity", "spectrum", "charter",
        "cox", "optimum", "frontier", "centurylink", "verizon fios", "att fiber",
        # Phone
        "phone", "wireless", "cellular", "mobile", "verizon", "att", "at&t",
        "t-mobile", "tmobile", "sprint", "boost", "cricket", "metro pcs",
        # Housing
        "rent", "rental", "lease", "landlord", "property management", "apartment",
        "mortgage", "loan payment", "hoa", "homeowner association",
        # Insurance
        "insurance", "geico", "state farm", "allstate", "progressive", "farmers",
        "liberty mutual", "nationwide", "usaa",
        # Subscriptions
        "subscription", "membership", "recurring", "monthly", "annual"
    ],
}

