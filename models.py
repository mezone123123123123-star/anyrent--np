from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), default='')
    phone = db.Column(db.String(30), default='')
    location = db.Column(db.String(150), default='')
    bio = db.Column(db.String(500), default='')
    profile_pic = db.Column(db.String(255), default='')
    verification_status = db.Column(db.String(20), default='unverified')
    national_id_image = db.Column(db.String(255), default='')
    selfie_image = db.Column(db.String(255), default='')
    date_of_birth = db.Column(db.Date, nullable=True)
    citizenship = db.Column(db.String(100), default='')
    age_verified = db.Column(db.Boolean, default=False)
    citizenship_verified = db.Column(db.Boolean, default=False)
    face_verified = db.Column(db.Boolean, default=False)
    predicted_age = db.Column(db.Integer, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_verified(self):
        return self.verification_status == 'verified'


class AgeTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    age_label = db.Column(db.Integer, nullable=False)
    phash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='age_templates')


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(80), default='Item')
    description = db.Column(db.String(600), default='')
    price = db.Column(db.Integer, nullable=False, default=0)
    deposit = db.Column(db.Integer, default=0)
    quantity = db.Column(db.Integer, default=1)
    location = db.Column(db.String(150), default='')
    rating = db.Column(db.Float, default=0.0)
    reviews = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500), default='')
    video = db.Column(db.String(500), default='')
    available = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref='items')


class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    price_per_day = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Integer, default=0)
    # deposit_amount: computed as 20% of total_amount at rental creation
    deposit_amount = db.Column(db.Integer, default=0)
    # admin_commission: admin receives 15% of deposit_amount
    admin_commission = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item', backref='rentals')
    renter = db.relationship('User', foreign_keys=[renter_id], backref='rentals_made')
    owner = db.relationship('User', foreign_keys=[owner_id], backref='rentals_received')


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    body = db.Column(db.String(1000), default='')
    image = db.Column(db.String(500), default='')
    video = db.Column(db.String(500), default='')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    item = db.relationship('Item', backref='messages')


class SavedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='saved_items')
    item = db.relationship('Item', backref='saved_by')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(800), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item', backref='reviews_list')
    user = db.relationship('User', backref='reviews_made')


class ListingChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    proposer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    new_data = db.Column(db.Text, nullable=False)  # JSON blob of proposed changes
    prev_is_approved = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item', backref='change_requests')
    proposer = db.relationship('User', backref='listing_changes')

class CommissionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rental = db.relationship('Rental', backref='commission_record')
