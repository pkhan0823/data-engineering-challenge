from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import asyncio
import json
import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from datetime import datetime
import random
import os
from sqlalchemy import inspect

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///machinery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create images directory
IMAGES_DIR = 'static/images'
os.makedirs(IMAGES_DIR, exist_ok=True)

# Category to image mapping
CATEGORY_IMAGES = {
    'cnc': [
        'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092161562-40038fbba5e7?w=400&h=300&fit=crop',
    ],
    'lathe': [
        'https://images.unsplash.com/photo-1581092162561-40038fbba5e7?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092913537-8b23f7eb63d4?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092917550-e323b2c0a613?w=400&h=300&fit=crop',
    ],
    'drill': [
        'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092162561-40038fbba5e7?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581093918056-0c4c3acd3789?w=400&h=300&fit=crop',
    ],
    'press': [
        'https://images.unsplash.com/photo-1621905251918-48416bd8575a?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092913537-8b23f7eb63d4?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092162561-40038fbba5e7?w=400&h=300&fit=crop',
    ],
    'grinder': [
        'https://images.unsplash.com/photo-1581092915550-e323b2c0a613?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092913537-8b23f7eb63d4?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1581092162561-40038fbba5e7?w=400&h=300&fit=crop',
    ]
}

# Database Model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False, index=True)
    supplier = db.Column(db.String(255), nullable=False)
    price_usd = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    min_order = db.Column(db.Integer, default=1)
    rating = db.Column(db.Float, default=4.5)
    specs = db.Column(db.Text)
    image_url = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'supplier': self.supplier,
            'price_usd': self.price_usd,
            'category': self.category,
            'location': self.location,
            'description': self.description,
            'min_order': self.min_order,
            'rating': self.rating,
            'specs': self.specs,
            'image_url': self.image_url
        }

class MachineryData(BaseModel):
    product_name: str = Field(..., description="The official product title")
    supplier: str = Field(..., description="Name of the selling company")
    price_usd: str = Field(..., description="Price string (e.g. $500.00)")

# Sample data to populate database
SAMPLE_PRODUCTS = [
    {
        "product_name": "CNC Vertical Machining Center 3 Axis",
        "supplier": "Shanghai Precision Machinery Ltd.",
        "price_usd": "$2,500.00",
        "category": "cnc",
        "location": "china",
        "description": "High precision 3-axis CNC vertical machining center with automatic tool changer",
        "min_order": 1,
        "rating": 4.5,
        "specs": "Work area: 1000x500mm, Spindle speed: 6000 RPM"
    },
    {
        "product_name": "Industrial CNC Milling Machine 5-Axis",
        "supplier": "Bangalore Tech Industries",
        "price_usd": "$4,200.00",
        "category": "cnc",
        "location": "india",
        "description": "Heavy-duty 5-axis CNC milling machine for industrial applications",
        "min_order": 1,
        "rating": 4.3,
        "specs": "Work area: 1500x800mm, Spindle speed: 8000 RPM"
    },
    {
        "product_name": "CNC Router Machine 3D Carving",
        "supplier": "Zhejiang Industrial Tech",
        "price_usd": "$1,800.00",
        "category": "cnc",
        "location": "china",
        "description": "Wood and plastic carving CNC router for detailed work",
        "min_order": 1,
        "rating": 4.6,
        "specs": "Work area: 1300x2500mm, Spindle: 3kW"
    },
    {
        "product_name": "CNC 4-Axis Lathe Turret",
        "supplier": "Bangalore Tech Industries",
        "price_usd": "$4,800.00",
        "category": "cnc",
        "location": "india",
        "description": "4-axis CNC lathe with automatic turret indexing",
        "min_order": 1,
        "rating": 4.7,
        "specs": "Chuck size: 200mm, Spindle speed: 3000 RPM"
    },
    {
        "product_name": "Desktop Mini CNC Machine",
        "supplier": "Guangzhou Electronics",
        "price_usd": "$600.00",
        "category": "cnc",
        "location": "china",
        "description": "Compact desktop CNC for hobby and small business",
        "min_order": 1,
        "rating": 4.2,
        "specs": "Work area: 300x200mm, USB connection"
    },
    {
        "product_name": "Heavy Duty Metal Lathe",
        "supplier": "German Precision Engineering",
        "price_usd": "$5,800.00",
        "category": "lathe",
        "location": "germany",
        "description": "Precision metal lathe for turning operations",
        "min_order": 1,
        "rating": 4.8,
        "specs": "Swing: 500mm, Distance between centers: 1000mm"
    },
    {
        "product_name": "Automatic Bar Feeding Lathe",
        "supplier": "Taiwan Machine Tools",
        "price_usd": "$3,500.00",
        "category": "lathe",
        "location": "taiwan",
        "description": "Automatic lathe with bar feeder for mass production",
        "min_order": 1,
        "rating": 4.5,
        "specs": "Chuck size: 150mm, Max spindle speed: 3000 RPM"
    },
    {
        "product_name": "Precision Radial Drill Machine",
        "supplier": "USA Manufacturing Corp",
        "price_usd": "$4,200.00",
        "category": "drill",
        "location": "usa",
        "description": "Industrial radial drill for large-scale operations",
        "min_order": 1,
        "rating": 4.6,
        "specs": "Arm reach: 1500mm, Max spindle speed: 2000 RPM"
    },
    {
        "product_name": "Vertical Drilling Machine",
        "supplier": "Shanghai Precision Machinery Ltd.",
        "price_usd": "$2,900.00",
        "category": "drill",
        "location": "china",
        "description": "Heavy-duty vertical drilling for steel and metal",
        "min_order": 1,
        "rating": 4.3,
        "specs": "Table size: 1000x500mm, Max drilling diameter: 50mm"
    },
    {
        "product_name": "Hydraulic Press 100 Ton",
        "supplier": "Shanghai Precision Machinery Ltd.",
        "price_usd": "$6,500.00",
        "category": "press",
        "location": "china",
        "description": "100-ton hydraulic press with precision pressure control",
        "min_order": 1,
        "rating": 4.4,
        "specs": "Max pressure: 315 MPa, Platen area: 400x400mm"
    },
]

def get_random_image_for_category(category):
    """Get a random image URL for a product category"""
    images = CATEGORY_IMAGES.get(category.lower(), CATEGORY_IMAGES['cnc'])
    return random.choice(images)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if image_url column exists, if not add it
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('products')]
        
        if 'image_url' not in columns:
            print("⚠️ Adding image_url column to existing database...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE products ADD COLUMN image_url VARCHAR(500) DEFAULT ''"))
                conn.commit()
            print("✅ image_url column added successfully")
        
        # Check if data already exists
        if Product.query.first() is None:
            for product in SAMPLE_PRODUCTS:
                product['image_url'] = get_random_image_for_category(product['category'])
                new_product = Product(**product)
                db.session.add(new_product)
            db.session.commit()
            print(f"✅ Database initialized with {len(SAMPLE_PRODUCTS)} products")
        else:
            # Update existing products without images
            products_without_images = Product.query.filter(Product.image_url == '').all()
            if products_without_images:
                print(f"⚠️ Updating {len(products_without_images)} products with images...")
                for product in products_without_images:
                    product.image_url = get_random_image_for_category(product.category)
                db.session.commit()
                print("✅ Products updated with images")
            
            count = Product.query.count()
            print(f"✅ Database already has {count} products")

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering and pagination"""
    category = request.args.get('category', '').lower()
    location = request.args.get('location', '').lower()
    search = request.args.get('search', '').lower()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Product.query
    
    if category:
        query = query.filter(Product.category == category)
    
    if location:
        query = query.filter(Product.location == location)
    
    if search:
        query = query.filter(
            (Product.product_name.ilike(f'%{search}%')) |
            (Product.supplier.ilike(f'%{search}%')) |
            (Product.description.ilike(f'%{search}%'))
        )
    
    # Pagination
    paginated = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'count': paginated.total,
        'page': page,
        'per_page': per_page,
        'total_pages': paginated.pages,
        'products': [p.to_dict() for p in paginated.items]
    })

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    """Get single product details"""
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    return jsonify({
        'success': True,
        'product': product.to_dict()
    })

@app.route('/api/contact', methods=['POST'])
def contact_supplier():
    """Handle supplier contact requests"""
    data = request.json
    product_id = data.get('product_id')
    buyer_name = data.get('buyer_name')
    buyer_email = data.get('buyer_email')
    message = data.get('message')
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    # Log the contact
    print(f"\n📧 NEW CONTACT REQUEST")
    print(f"Product: {product.product_name}")
    print(f"Supplier: {product.supplier}")
    print(f"From: {buyer_name} ({buyer_email})")
    print(f"Message: {message}")
    print(f"Timestamp: {datetime.now()}\n")
    
    return jsonify({
        'success': True,
        'message': f'Your inquiry has been sent to {product.supplier}'
    })

@app.route('/api/scrape', methods=['POST'])
def scrape_alibaba():
    """Add new products from scraping"""
    try:
        # Generate 10 random new products for demo
        new_products_count = 10
        categories = ['cnc', 'lathe', 'drill', 'press', 'grinder']
        locations = ['china', 'india', 'usa', 'germany', 'japan', 'taiwan']
        
        for i in range(new_products_count):
            category = random.choice(categories)
            product = Product(
                product_name=f"Industrial Machine Model {i+1}",
                supplier=f"Supplier Company {random.randint(1, 50)}",
                price_usd=f"${random.randint(500, 10000)}.00",
                category=category,
                location=random.choice(locations),
                description="High-quality industrial machinery equipment",
                min_order=random.randint(1, 5),
                rating=round(random.uniform(4.0, 5.0), 1),
                specs="Standard industrial specifications",
                image_url=get_random_image_for_category(category)
            )
            db.session.add(product)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully added {new_products_count} new products',
            'total_products': Product.query.count()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get marketplace statistics"""
    total_products = Product.query.count()
    total_suppliers = db.session.query(Product.supplier).distinct().count()
    
    categories = db.session.query(Product.category, db.func.count(Product.id)).group_by(Product.category).all()
    locations = db.session.query(Product.location, db.func.count(Product.id)).group_by(Product.location).all()
    
    return jsonify({
        'success': True,
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'categories': {cat: count for cat, count in categories},
        'locations': {loc: count for loc, count in locations}
    })

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/', methods=['GET'])
def index():
    """Serve the frontend"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting to frontend...</title>
        <script>
            window.location.href = '/frontend';
        </script>
    </head>
    </html>
    '''

@app.route('/frontend', methods=['GET'])
def serve_frontend():
    """Serve the HTML frontend"""
    try:
        return open('index.html', 'r').read()
    except:
        return jsonify({'error': 'index.html not found'}), 404

if __name__ == '__main__':
    init_db()
    with app.app_context():
        total_products = Product.query.count()
        print("🚀 B2B Marketplace Backend Starting...")
        print("📍 API running at http://localhost:5000")
        print("🌐 Frontend at http://localhost:5000/frontend")
        print(f"📦 Total products in database: {total_products}")
    app.run(debug=True, host='0.0.0.0', port=5000)