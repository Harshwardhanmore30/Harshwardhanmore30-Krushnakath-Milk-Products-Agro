from models.database import db, Product, ProductSpecification, MLProduct
from sqlalchemy import or_
import pandas as pd
import pickle
import os
from config import Config

class ProductService:
    """Service class for product operations"""
    
    @staticmethod
    def get_all_products():
        """Get all products with their specifications"""
        try:
            products = Product.query.all()
            return products
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []
    
    @staticmethod
    def get_product_by_id(product_id):
        """Get product by ID with specifications"""
        try:
            product = Product.query.get(product_id)
            return product
        except Exception as e:
            print(f"Error fetching product {product_id}: {e}")
            return None
    
    @staticmethod
    def search_products(query):
        """Search products by name or description"""
        try:
            products = Product.query.filter(
                or_(
                    Product.name.ilike(f'%{query}%'),
                    Product.description.ilike(f'%{query}%'),
                    Product.category.ilike(f'%{query}%')
                )
            ).all()
            return products
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    @staticmethod
    def get_products_by_category(category):
        """Get products by category"""
        try:
            products = Product.query.filter_by(category=category).all()
            return products
        except Exception as e:
            print(f"Error fetching products by category: {e}")
            return []
    
    @staticmethod
    def get_products_by_ids(product_ids):
        """Get a list of products by their IDs"""
        try:
            if not product_ids:
                return []
            
            products = Product.query.filter(Product.id.in_(product_ids)).all()
            return products
        except Exception as e:
            print(f"Error fetching products by IDs: {e}")
            return []
    
    @staticmethod
    def get_products_by_names(product_names):
        """Get a list of products by their names, preserving order."""
        try:
            if not product_names:
                return []
            
            # Fetch all products that match the names
            products = Product.query.filter(Product.name.in_(product_names)).all()
            
            # Create a mapping from name to product object to preserve order
            product_map = {p.name: p for p in products}
            
            # Build the final list in the same order as the recommendations
            ordered_products = [product_map[name] for name in product_names if name in product_map]
            
            return ordered_products
        except Exception as e:
            print(f"Error fetching products by names: {e}")
            return []
    
    @staticmethod
    def create_product(name, price, description, image, stock=100, category=None, specifications=None):
        """Create a new product"""
        try:
            product = Product(
                name=name,
                price=price,
                description=description,
                image=image,
                stock=stock,
                category=category
            )
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Add specifications if provided
            if specifications:
                for spec in specifications:
                    product_spec = ProductSpecification(
                        product_id=product.id,
                        feature=spec['feature'],
                        value=spec['value']
                    )
                    db.session.add(product_spec)
            
            db.session.commit()
            return True, "Product created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating product: {str(e)}"
    
    @staticmethod
    def update_product(product_id, **kwargs):
        """Update product information"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found"
            
            # Update product fields
            for key, value in kwargs.items():
                if hasattr(product, key) and key != 'id':
                    setattr(product, key, value)
            
            db.session.commit()
            return True, "Product updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating product: {str(e)}"
    
    @staticmethod
    def delete_product(product_id):
        """Delete a product"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found"
            
            db.session.delete(product)
            db.session.commit()
            return True, "Product deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting product: {str(e)}"
    
    @staticmethod
    def update_stock(product_id, quantity):
        """Update product stock"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found"
            
            product.stock = max(0, product.stock + quantity)
            db.session.commit()
            return True, "Stock updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating stock: {str(e)}"
    
    @staticmethod
    def get_low_stock_products(threshold=5):
        """Get products with low stock"""
        try:
            products = Product.query.filter(Product.stock <= threshold).all()
            return products
        except Exception as e:
            print(f"Error fetching low stock products: {e}")
            return []
    
    @staticmethod
    def get_ml_recommendations(product_name, num_recommendations=5):
        """Get ML-based product recommendations"""
        try:
            # Load ML models
            if not os.path.exists(Config.TFIDF_VECTORIZER_PATH) or not os.path.exists(Config.COSINE_SIM_PATH):
                return []
            
            with open(Config.TFIDF_VECTORIZER_PATH, 'rb') as f:
                tfidf_vectorizer = pickle.load(f)
            
            with open(Config.COSINE_SIM_PATH, 'rb') as f:
                cosine_sim = pickle.load(f)
            
            # Get ML products from database
            ml_products = MLProduct.query.all()
            if not ml_products:
                return []
            
            # Find the product index
            product_names = [p.product_name for p in ml_products]
            try:
                product_idx = product_names.index(product_name)
            except ValueError:
                return []
            
            # Get similarity scores
            sim_scores = list(enumerate(cosine_sim[product_idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:num_recommendations+1]
            
            # Get recommended products
            recommended_products = []
            for idx, score in sim_scores:
                if idx < len(ml_products):
                    recommended_products.append({
                        'product_id': ml_products[idx].product_id,
                        'product_name': ml_products[idx].product_name,
                        'category': ml_products[idx].category,
                        'description': ml_products[idx].description,
                        'price': ml_products[idx].price,
                        'similarity_score': score
                    })
            
            return recommended_products
            
        except Exception as e:
            print(f"Error getting ML recommendations: {e}")
            return []
    
    @staticmethod
    def migrate_products_from_csv(csv_file):
        """Migrate products from CSV file to database"""
        try:
            df = pd.read_csv(csv_file)
            
            for _, row in df.iterrows():
                # Check if product already exists
                existing_product = Product.query.filter_by(name=row['name']).first()
                if existing_product:
                    continue
                
                # Create product
                product = Product(
                    name=row['name'],
                    price=float(row['price']),
                    description=row['description'],
                    image=row['image'],
                    stock=int(row.get('stock', 100)),
                    category=row.get('category', 'Dairy')
                )
                
                db.session.add(product)
                db.session.flush()
                
                # Add specifications if available
                if 'specifications' in row and pd.notna(row['specifications']):
                    specs = eval(row['specifications'])
                    for spec in specs:
                        product_spec = ProductSpecification(
                            product_id=product.id,
                            feature=spec['feature'],
                            value=spec['value']
                        )
                        db.session.add(product_spec)
            
            db.session.commit()
            return True, "Products migrated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error migrating products: {str(e)}"
    
    @staticmethod
    def migrate_ml_products_from_csv(csv_file):
        """Migrate ML products from CSV file to database"""
        try:
            df = pd.read_csv(csv_file)
            
            for _, row in df.iterrows():
                # Check if ML product already exists
                existing_product = MLProduct.query.filter_by(product_name=row['product_name']).first()
                if existing_product:
                    continue
                
                # Create ML product
                ml_product = MLProduct(
                    product_id=row.get('product_id', 0),
                    product_name=row['product_name'],
                    category=row['category'],
                    description=row['description'],
                    ingredients=row['ingredients'],
                    price=float(row['price']),
                    combined_features=row['combined_features']
                )
                
                db.session.add(ml_product)
            
            db.session.commit()
            return True, "ML products migrated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error migrating ML products: {str(e)}" 