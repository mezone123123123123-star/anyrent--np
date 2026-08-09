from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect
from models import db, User, Item
from profile import profile_bp
from marketplace import marketplace_bp
from verification import verification_bp

app = Flask(__name__, static_folder='templates/static')
app.config['SECRET_KEY'] = 'your-super-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['MAX_CONTENT_LENGTH'] = 120 * 1024 * 1024

db.init_app(app)
app.register_blueprint(profile_bp)
app.register_blueprint(marketplace_bp)
app.register_blueprint(verification_bp)
login_manager = LoginManager()
login_manager.login_view = 'auth'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

REQUIRED_COLUMNS = {
    'user': ['username', 'email', 'password_hash', 'full_name', 'phone',
             'location', 'bio', 'profile_pic', 'verification_status',
             'national_id_image', 'selfie_image', 'date_of_birth', 'citizenship',
             'age_verified', 'citizenship_verified', 'face_verified', 'predicted_age', 'is_admin', 'created_at'],
    'item': ['owner_id', 'name', 'category', 'price', 'deposit', 'location',
             'rating', 'reviews', 'image', 'available', 'is_approved', 'created_at'],
    'age_template': ['user_id', 'image_filename', 'age_label', 'phash', 'created_at'],
}


def schema_is_current():
    """Return True if every required table exists and has the needed columns."""
    inspector = inspect(db.engine)
    existing = set(inspector.get_table_names())
    for table, columns in REQUIRED_COLUMNS.items():
        if table not in existing:
            return False
        present = {c['name'] for c in inspector.get_columns(table)}
        if not set(columns).issubset(present):
            return False
    return True


with app.app_context():
    if not schema_is_current():
        print('[AnyRent] Detected an outdated database schema — recreating tables '
              '(existing data is demo data and will be reseeded).')
        db.drop_all()

    db.create_all()

    if Item.query.count() == 0:
        owner = User.query.filter_by(email='demo@anyrent.com').first()
        if not owner:
            owner = User(
                username='AnyRentHQ',
                email='demo@anyrent.com',
                password_hash=generate_password_hash('demo-password', method='pbkdf2:sha256'),
                full_name='AnyRent Demo Owner',
                location='Kathmandu',
                bio='Curated demo listings for the community.',
                is_admin=True,
                verification_status='verified',
            )
            db.session.add(owner)
            db.session.flush()

        seed_items = [
            {'name': 'Sony Alpha Camera', 'category': 'Camera', 'type': 'Photography',
             'price': 1500, 'deposit': 10000, 'location': 'Kathmandu',
             'image': 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80',
             'description': 'Professional mirrorless camera perfect for photography, events and content creation.'},
            {'name': 'Canon EOS Camera', 'category': 'Camera', 'type': 'Photography',
             'price': 1200, 'deposit': 9000, 'location': 'Lalitpur',
             'image': 'https://images.unsplash.com/photo-1606986628253-2e37f5d8c6d5?auto=format&fit=crop&w=900&q=80',
             'description': 'Reliable DSLR camera suitable for photography and video projects.'},
            {'name': 'Fender Acoustic Guitar', 'category': 'Music', 'type': 'Musical Instrument',
             'price': 800, 'deposit': 5000, 'location': 'Kathmandu',
             'image': 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?auto=format&fit=crop&w=900&q=80',
             'description': 'Well-maintained acoustic guitar for performances, practice and recording.'},
            {'name': 'Mountain Bike', 'category': 'Bike', 'type': 'Cycling',
             'price': 600, 'deposit': 4000, 'location': 'Bhaktapur',
             'image': 'https://images.unsplash.com/photo-1541625602330-2277a4c46182?auto=format&fit=crop&w=900&q=80',
             'description': 'Mountain bike suitable for city rides, trails and weekend adventures.'},
            {'name': 'MacBook Pro', 'category': 'Electronics', 'type': 'Laptop',
             'price': 1800, 'deposit': 20000, 'location': 'Kathmandu',
             'image': 'https://images.unsplash.com/photo-1517336714739-489689fd1ca8?auto=format&fit=crop&w=900&q=80',
             'description': 'High-performance laptop for development, design and professional work.'},
            {'name': 'Portable Projector', 'category': 'Electronics', 'type': 'Projector',
             'price': 700, 'deposit': 6000, 'location': 'Kathmandu',
             'image': 'https://images.unsplash.com/photo-1535016120720-40c646be5580?auto=format&fit=crop&w=900&q=80',
             'description': 'Compact projector for presentations, movies, events and gatherings.'},
            {'name': 'DJ Controller', 'category': 'Music', 'type': 'DJ Equipment',
             'price': 1300, 'deposit': 12000, 'location': 'Kathmandu',
             'image': 'https://images.unsplash.com/photo-1571266028243-d220c9c3b12f?auto=format&fit=crop&w=900&q=80',
             'description': 'Professional DJ controller for parties, events and music production.'},
            {'name': 'Camping Tent', 'category': 'Other', 'type': 'Camping',
             'price': 500, 'deposit': 3000, 'location': 'Lalitpur',
             'image': 'https://images.unsplash.com/photo-1504851149312-7a075b496cc7?auto=format&fit=crop&w=900&q=80',
             'description': 'Comfortable camping tent suitable for weekend trips and outdoor adventures.'},
        ]
        for s in seed_items:
            db.session.add(Item(owner_id=owner.id, rating=4.8 + (0.1 * (seed_items.index(s) % 3)),
                                reviews=6 + (seed_items.index(s) * 3), **s))
        db.session.commit()

    # Run DB migration and template indexing to ensure phash column and index exist
    try:
        import runpy, os
        basedir = os.path.dirname(__file__)
        migrate_path = os.path.join(basedir, 'migrate_add_phash.py')
        indexer_path = os.path.join(basedir, 'index_templates_to_db.py')
        listing_change_migrate = os.path.join(basedir, 'migrate_create_listing_change.py')
        print('[AnyRent] Running DB migration (migrate_add_phash.py)')
        runpy.run_path(migrate_path, run_name='__main__')
        print('[AnyRent] Running template indexer (index_templates_to_db.py)')
        runpy.run_path(indexer_path, run_name='__main__')
        print('[AnyRent] Ensuring listing change migration (migrate_create_listing_change.py)')
        runpy.run_path(listing_change_migrate, run_name='__main__')
        print('[AnyRent] Running quantity migration (migrate_add_quantity.py)')
        quantity_migrate = os.path.join(basedir, 'migrate_add_quantity.py')
        runpy.run_path(quantity_migrate, run_name='__main__')
        print('[AnyRent] Running video migration (migrate_add_video.py)')
        video_migrate = os.path.join(basedir, 'migrate_add_video.py')
        runpy.run_path(video_migrate, run_name='__main__')
        print('[AnyRent] Running message attachments migration (migrate_add_message_attachments.py)')
        msg_migrate = os.path.join(basedir, 'migrate_add_message_attachments.py')
        runpy.run_path(msg_migrate, run_name='__main__')
    except Exception as e:
        print('[AnyRent] Failed to run migration/indexer:', e)

@app.route('/')
def home():
    return render_template('index.html', active_nav='home')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if current_user.is_authenticated:
        return render_template('auth.html', active_tab='dashboard', active_nav='home', name=current_user.username)

    return render_template('auth.html', active_tab='login', active_nav='home')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        login_user(user, remember=True)
        session['age_verified'] = user.age_verified
        session['citizenship_verified'] = user.citizenship_verified
        session['face_verified'] = user.face_verified
        session['verified'] = user.age_verified and user.citizenship_verified and user.face_verified
        return redirect(url_for('profile.profile'))
    else:
        flash('Invalid email or password. Please try again.', 'danger')
        return render_template('auth.html', active_tab='login', active_nav='home')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    accept_terms = request.form.get('accept_terms')

    if accept_terms != 'on':
        flash('You must accept the Terms & Conditions to create an account.', 'danger')
        return render_template('auth.html', active_tab='signup', active_nav='home')

    user_by_email = User.query.filter_by(email=email).first()
    user_by_username = User.query.filter_by(username=username).first()
    if user_by_email:
        flash('Email address already registered.', 'danger')
        return render_template('auth.html', active_tab='signup', active_nav='home')
    if user_by_username:
        flash('Username already taken.', 'danger')
        return render_template('auth.html', active_tab='signup', active_nav='home')

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, email=email, password_hash=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()

    flash('Account created successfully! Please log in.', 'success')
    return render_template('auth.html', active_tab='login', active_nav='home')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/index')
def index():
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html', active_nav='about')

@app.route('/faq')
def faq():
    return render_template('faq.html', active_nav='faq')

if __name__ == '__main__':
    app.run(debug=True)