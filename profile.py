import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import json
from models import db, User, Item, Rental, Message, SavedItem, Review, CommissionRecord, ListingChange

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'm4v'}

DEFAULT_ITEM_IMAGE = ("https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e"
                      "?auto=format&fit=crop&w=900&q=80")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def save_message_file(file, prefix):
    """Save an uploaded message attachment into the uploads folder."""
    fname = secure_filename(file.filename)
    stored = f"{prefix}_{current_user.id}_{fname}"
    upload_dir = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, stored))
    return stored


def load_dashboard():
    """Collect every piece of data the dashboard renders in one place."""
    uid = current_user.id

    my_items = (Item.query.filter_by(owner_id=uid)
                .order_by(Item.created_at.desc()).all())

    rentals_in = (Rental.query.filter_by(renter_id=uid)
                  .order_by(Rental.created_at.desc()).all())

    rentals_out = (Rental.query.filter_by(owner_id=uid)
                   .order_by(Rental.created_at.desc()).all())

    saved_items = [s.item for s in
                   SavedItem.query.filter_by(user_id=uid)
                   .order_by(SavedItem.created_at.desc()).all()]

    messages = (Message.query.filter(
                    (Message.sender_id == uid) | (Message.receiver_id == uid))
                .order_by(Message.created_at.desc()).all())

    conversations = {}
    for m in messages:
        other_id = m.sender_id if m.receiver_id == uid else m.receiver_id
        key = (other_id, m.item_id)
        conversations.setdefault(key, []).append(m)

    convo_list = []
    for (other_id, item_id), msgs in conversations.items():
        convo_list.append({
            'other': User.query.get(other_id),
            'item': Item.query.get(item_id) if item_id else None,
            'messages': list(reversed(msgs)),
            'unread': sum(1 for m in msgs if m.receiver_id == uid and not m.is_read),
        })
    convo_list.sort(key=lambda c: c['messages'][-1].created_at, reverse=True)

    for c in convo_list:
        for m in c['messages']:
            if m.receiver_id == uid and not m.is_read:
                m.is_read = True
    if convo_list:
        db.session.commit()

    earnings = sum(r.total_amount for r in rentals_out
                   if r.status in ('approved', 'completed'))
    # admin earnings (commission) across all rentals that are approved/completed
    admin_earnings = 0
    admin_commission_count = 0
    if current_user.is_admin:
        admin_rows = Rental.query.filter(Rental.status.in_(['approved','completed'])).all()
        admin_earnings = sum((r.admin_commission or 0) for r in admin_rows)
        admin_commission_count = sum(1 for r in admin_rows if (r.admin_commission or 0) > 0)

    rented_count = len([r for r in rentals_in if r.status not in ('cancelled', 'declined')])
    pending_requests = sum(1 for r in rentals_out if r.status == 'pending')
    unread_total = sum(c['unread'] for c in convo_list)

    session['age_verified'] = current_user.age_verified
    session['citizenship_verified'] = current_user.citizenship_verified
    session['face_verified'] = current_user.face_verified
    session['verified'] = (current_user.age_verified and current_user.citizenship_verified
                           and current_user.face_verified)

    pending_verifications = []
    pending_listing_changes = []
    pending_rentals = []
    if current_user.is_admin:
        pending_verifications = (User.query
                                 .filter_by(verification_status='pending')
                                 .order_by(User.created_at.desc()).all())
        pending_items = (Item.query.filter_by(is_approved=False).order_by(Item.created_at.desc()).all())
        pending_listing_changes = (ListingChange.query.filter_by(status='pending')
                                   .order_by(ListingChange.created_at.desc()).all())
        pending_rentals = (Rental.query.filter_by(status='pending')
                           .order_by(Rental.created_at.desc()).all())
    else:
        pending_verifications = []
        pending_items = []
        pending_listing_changes = []
        pending_rentals = []

    return {
        'user': current_user,
        'my_items': my_items,
        'rentals_in': rentals_in,
        'rentals_out': rentals_out,
        'saved_items': saved_items,
        'conversations': convo_list,
        'earnings': earnings,
        'admin_earnings': admin_earnings,
        'admin_commission_count': admin_commission_count,
        'rented_count': rented_count,
        'pending_requests': pending_requests,
        'unread_total': unread_total,
        'pending_verifications': pending_verifications,
        'pending_items': pending_items,
        'pending_listing_changes': pending_listing_changes,
        'pending_rentals': pending_rentals,
    }


@profile_bp.route('/profile')
@login_required
def profile():
    data = load_dashboard()
    return render_template('profile.html', active_tab='profile', **data)


@profile_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    location = request.form.get('location', '').strip()
    bio = request.form.get('bio', '').strip()

    current_user.full_name = full_name
    current_user.phone = phone
    current_user.location = location
    current_user.bio = bio

    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile.profile'))


@profile_bp.route('/profile/picture', methods=['POST'])
@login_required
def upload_picture():
    file = request.files.get('profile_pic')

    if not file or file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('profile.profile'))

    if not allowed_file(file.filename):
        flash('Invalid image type. Use PNG, JPG, JPEG, GIF or WEBP.', 'danger')
        return redirect(url_for('profile.profile'))

    filename = secure_filename(file.filename)
    stored_name = f"user_{current_user.id}_{filename}"

    upload_dir = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    file.save(os.path.join(upload_dir, stored_name))

    current_user.profile_pic = stored_name
    db.session.commit()

    flash('Profile picture updated!', 'success')
    return redirect(url_for('profile.profile'))


@profile_bp.route('/profile/verify', methods=['POST'])
@login_required
def verify_identity():
    file = request.files.get('national_id')

    if not file or file.filename == '':
        flash('Please select an image of your national ID card.', 'danger')
        return redirect(url_for('profile.profile') + '#verify')

    if not allowed_file(file.filename):
        flash('Invalid image type. Use PNG, JPG, JPEG, GIF or WEBP.', 'danger')
        return redirect(url_for('profile.profile') + '#verify')

    if current_user.is_verified:
        flash('Your account is already verified.', 'success')
        return redirect(url_for('profile.profile') + '#verify')

    filename = secure_filename(file.filename)
    stored_name = f"nid_{current_user.id}_{filename}"

    upload_dir = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    file.save(os.path.join(upload_dir, stored_name))

    current_user.national_id_image = stored_name
    current_user.verification_status = 'pending'
    db.session.commit()

    flash('National ID uploaded. Our team will review it shortly.', 'success')
    return redirect(url_for('profile.profile') + '#verify')


@profile_bp.route('/admin/verify/<int:user_id>/<action>', methods=['POST'])
@login_required
def admin_verify(user_id, action):
    if not current_user.is_admin:
        flash('You do not have permission to do that.', 'danger')
        return redirect(url_for('profile.profile') + '#verify')

    target = User.query.get_or_404(user_id)

    if action == 'approve':
        target.verification_status = 'verified'
        flash(f'@{target.username} is now verified.', 'success')
    elif action == 'reject':
        target.verification_status = 'unverified'
        flash(f'@{target.username} verification rejected.', 'danger')
    else:
        flash('Unknown action.', 'danger')

    db.session.commit()
    return redirect(url_for('profile.profile') + '#verify')


@profile_bp.route('/profile/items/add', methods=['POST'])
@login_required
def add_item():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    item_type = request.form.get('type', '').strip()
    price = request.form.get('price', '').strip()
    deposit = request.form.get('deposit', '').strip()
    quantity = request.form.get('quantity', '').strip()
    location = request.form.get('location', '').strip()
    image = request.form.get('image', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not price:
        flash('Item name and price are required.', 'danger')
        return redirect(url_for('profile.profile') + '#listings')

    try:
        price = int(price)
        deposit = int(deposit) if deposit else 0
        quantity = int(quantity) if quantity else 1
    except ValueError:
        flash('Price, deposit and quantity must be numbers.', 'danger')
        return redirect(url_for('profile.profile') + '#listings')

    if price <= 0:
        flash('Price must be greater than zero.', 'danger')
        return redirect(url_for('profile.profile') + '#listings')

    if quantity < 1:
        flash('Quantity must be at least 1.', 'danger')
        return redirect(url_for('profile.profile') + '#listings')

    video = ''
    video_file = request.files.get('video')
    if video_file and video_file.filename:
        if not allowed_video(video_file.filename):
            flash('Invalid video type. Use MP4, WebM, OGG, MOV or M4V.', 'danger')
            return redirect(url_for('profile.profile') + '#listings')
        vname = secure_filename(video_file.filename)
        vstored = f"item_video_{current_user.id}_{vname}"
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        video_file.save(os.path.join(upload_dir, vstored))
        video = vstored

    item = Item(
        owner_id=current_user.id,
        name=name,
        category=category or 'Other',
        type=item_type or 'Item',
        description=description,
        price=price,
        deposit=deposit,
        quantity=quantity,
        location=location or 'Kathmandu',
        image=image or DEFAULT_ITEM_IMAGE,
        video=video,
    )
    db.session.add(item)
    db.session.commit()

    flash(f'"{name}" is now live on the marketplace!', 'success')
    return redirect(url_for('profile.profile') + '#listings')


def consume_item_stock(item):
    """Decrement stock by one. When stock hits zero the item is hidden from
    the marketplace but KEPT in the database so it stays visible on the
    owner's dashboard (under "My listings")."""
    item.quantity = max((item.quantity or 1) - 1, 0)
    if item.quantity > 0:
        return False

    # Hide from the marketplace instead of deleting the record.
    item.available = False
    item.is_approved = True
    return True


@profile_bp.route('/profile/rentals/<int:rental_id>/<action>', methods=['POST'])
@login_required
def rental_action(rental_id, action):
    rental = Rental.query.get_or_404(rental_id)
    uid = current_user.id

    if action in ('approve', 'decline', 'complete'):
        if rental.owner_id != uid:
            flash('You can only manage requests on your own items.', 'danger')
            return redirect(url_for('profile.profile') + '#rentals')

        if action == 'approve' and rental.status == 'pending':
            rental.status = 'approved'
            # create commission record if not present and admin_commission > 0
            if getattr(rental, 'admin_commission', 0):
                existing = CommissionRecord.query.filter_by(rental_id=rental.id).first()
                if not existing:
                    db.session.add(CommissionRecord(rental_id=rental.id, amount=rental.admin_commission))
            if consume_item_stock(rental.item):
                flash('Request approved — this item is now fully rented out and removed from the marketplace.', 'success')
            else:
                flash('Request approved — the item is now reserved.', 'success')
        elif action == 'decline' and rental.status == 'pending':
            rental.status = 'declined'
            flash('Request declined.', 'success')
        elif action == 'complete' and rental.status == 'approved':
            rental.status = 'completed'
            # ensure commission record exists on completion as well
            if getattr(rental, 'admin_commission', 0):
                existing = CommissionRecord.query.filter_by(rental_id=rental.id).first()
                if not existing:
                    db.session.add(CommissionRecord(rental_id=rental.id, amount=rental.admin_commission))
            flash('Rental marked as completed.', 'success')
        else:
            flash('That action is not valid for this request.', 'danger')

    elif action == 'cancel':
        if rental.renter_id != uid:
            flash('You can only cancel your own requests.', 'danger')
            return redirect(url_for('profile.profile') + '#rentals')
        if rental.status == 'pending':
            rental.status = 'cancelled'
            flash('Rental request cancelled.', 'success')
        else:
            flash('Only pending requests can be cancelled.', 'danger')

    else:
        flash('Unknown action.', 'danger')

    db.session.commit()
    return redirect(url_for('profile.profile') + '#rentals')


@profile_bp.route('/profile/admin/item/<int:item_id>/<action>', methods=['POST'])
@login_required
def admin_item_action(item_id, action):
    if not current_user.is_admin:
        flash('You do not have permission to do that.', 'danger')
        return redirect(url_for('profile.profile'))
    item = Item.query.get_or_404(item_id)
    if action == 'approve' and not item.is_approved:
        item.is_approved = True
        flash(f'Item "{item.name}" approved and is now visible.', 'success')
    elif action == 'reject' and not item.is_approved:
        # simple reject: mark as unavailable
        item.available = False
        flash(f'Item "{item.name}" rejected and hidden from marketplace.', 'success')
    else:
        flash('Unknown action or invalid item state.', 'danger')
    db.session.commit()
    return redirect(url_for('profile.profile') + '#verify')


@profile_bp.route('/profile/admin/rental/<int:rental_id>/<action>', methods=['POST'])
@login_required
def admin_rental_action(rental_id, action):
    """Allow admins to manage rentals globally (approve/decline/complete)."""
    if not current_user.is_admin:
        flash('You do not have permission to do that.', 'danger')
        return redirect(url_for('profile.profile'))

    rental = Rental.query.get_or_404(rental_id)

    if action == 'approve' and rental.status == 'pending':
        rental.status = 'approved'
        if getattr(rental, 'admin_commission', 0):
            existing = CommissionRecord.query.filter_by(rental_id=rental.id).first()
            if not existing:
                db.session.add(CommissionRecord(rental_id=rental.id, amount=rental.admin_commission))
        if consume_item_stock(rental.item):
            flash('Rental request approved by admin — this item is now fully rented out and removed from the marketplace.', 'success')
        else:
            flash('Rental request approved by admin — the item is now reserved.', 'success')
    elif action == 'decline' and rental.status == 'pending':
        rental.status = 'declined'
        flash('Rental request declined by admin.', 'success')
    elif action == 'complete' and rental.status in ('approved','pending'):
        # allow admin to mark completed even if owner didn't
        rental.status = 'completed'
        if getattr(rental, 'admin_commission', 0):
            existing = CommissionRecord.query.filter_by(rental_id=rental.id).first()
            if not existing:
                db.session.add(CommissionRecord(rental_id=rental.id, amount=rental.admin_commission))
        flash('Rental marked as completed by admin.', 'success')
    else:
        flash('That action is not valid for this request.', 'danger')

    db.session.commit()
    return redirect(url_for('profile.profile') + '#verify')


@profile_bp.route('/profile/items/<int:item_id>/edit', methods=['GET','POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        flash('You can only edit your own items.', 'danger')
        return redirect(url_for('profile.profile') + '#listings')

    if request.method == 'GET':
        return render_template('edit_item.html', item=item)

    # POST: create a listing change request
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    item_type = request.form.get('type', '').strip()
    price = request.form.get('price', '').strip()
    deposit = request.form.get('deposit', '').strip()
    quantity = request.form.get('quantity', '').strip()
    location = request.form.get('location', '').strip()
    image = request.form.get('image', '').strip()
    description = request.form.get('description', '').strip()

    try:
        price = int(price) if price else item.price
        deposit = int(deposit) if deposit else item.deposit
        quantity = int(quantity) if quantity else item.quantity
    except ValueError:
        flash('Price, deposit and quantity must be numbers.', 'danger')
        return redirect(url_for('profile.profile') + '#listings')

    video = item.video
    video_file = request.files.get('video')
    if video_file and video_file.filename:
        if not allowed_video(video_file.filename):
            flash('Invalid video type. Use MP4, WebM, OGG, MOV or M4V.', 'danger')
            return redirect(url_for('profile.profile') + '#listings')
        vname = secure_filename(video_file.filename)
        vstored = f"item_video_{current_user.id}_{vname}"
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        video_file.save(os.path.join(upload_dir, vstored))
        video = vstored

    new_values = {
        'name': name or item.name,
        'category': category or item.category,
        'type': item_type or item.type,
        'price': price,
        'deposit': deposit,
        'quantity': quantity,
        'location': location or item.location,
        'image': image or item.image,
        'video': video,
        'description': description or item.description,
    }

    change = ListingChange(item_id=item.id, proposer_id=current_user.id,
                           new_data=json.dumps(new_values), prev_is_approved=bool(item.is_approved), status='pending')
    # hide the item until admin approves the update
    item.is_approved = False
    db.session.add(change)
    db.session.commit()

    flash('Your changes were submitted for admin review and are pending approval.', 'success')
    return redirect(url_for('profile.profile') + '#listings')


@profile_bp.route('/profile/admin/listing_change/<int:change_id>/<action>', methods=['POST'])
@login_required
def admin_listing_change_action(change_id, action):
    if not current_user.is_admin:
        flash('You do not have permission to do that.', 'danger')
        return redirect(url_for('profile.profile'))

    change = ListingChange.query.get_or_404(change_id)
    item = change.item

    if action == 'approve' and change.status == 'pending':
        try:
            data = json.loads(change.new_data)
        except Exception:
            data = {}

        # apply allowed fields
        for f in ('name','category','type','price','deposit','quantity','location','image','video','description'):
            if f in data:
                setattr(item, f if f != 'type' else 'type', data.get(f))

        item.is_approved = True
        change.status = 'approved'
        flash(f'Changes to "{item.name}" have been approved.', 'success')

    elif action == 'reject' and change.status == 'pending':
        change.status = 'rejected'
        # restore previous approval state
        item.is_approved = bool(change.prev_is_approved)
        flash(f'Change request for "{item.name}" was rejected.', 'danger')

    else:
        flash('Unknown action or invalid change state.', 'danger')

    db.session.commit()
    return redirect(url_for('profile.profile') + '#verify')


@profile_bp.route('/profile/messages/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id', '').strip()
    item_id = request.form.get('item_id', '').strip()
    body = request.form.get('body', '').strip()

    if not current_user.is_verified:
        flash('Verify your identity first — upload your national ID from your dashboard to message owners.', 'warning')
        return redirect(url_for('profile.profile') + '#verify')

    image = ''
    video = ''
    img_file = request.files.get('message_image')
    vid_file = request.files.get('message_video')

    if img_file and img_file.filename:
        if not allowed_file(img_file.filename):
            flash('Invalid image type. Use PNG, JPG, JPEG, GIF or WEBP.', 'danger')
            return redirect(url_for('profile.profile') + '#messages')
        image = save_message_file(img_file, 'msg_img')

    if vid_file and vid_file.filename:
        if not allowed_video(vid_file.filename):
            flash('Invalid video type. Use MP4, WebM, OGG, MOV or M4V.', 'danger')
            return redirect(url_for('profile.profile') + '#messages')
        video = save_message_file(vid_file, 'msg_vid')

    if not body and not image and not video:
        flash('Write a message or attach an image/video.', 'danger')
        return redirect(url_for('profile.profile') + '#messages')
    if not receiver_id:
        flash('Something went wrong sending the message.', 'danger')
        return redirect(url_for('profile.profile') + '#messages')

    msg = Message(
        sender_id=current_user.id,
        receiver_id=int(receiver_id),
        item_id=int(item_id) if item_id else None,
        body=body,
        image=image,
        video=video,
    )
    db.session.add(msg)
    db.session.commit()

    flash('Message sent!', 'success')
    return redirect(url_for('profile.profile') + '#messages')


@profile_bp.route('/profile/admin/commissions')
@login_required
def admin_commissions():
    if not current_user.is_admin:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('profile.profile'))

    import sqlite3, os
    DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''
        SELECT cr.id, cr.rental_id, cr.amount, cr.created_at, r.total_amount, r.deposit_amount, r.status,
               i.name as item_name, u1.username as renter, u2.username as owner
        FROM commission_record cr
        LEFT JOIN rental r ON r.id = cr.rental_id
        LEFT JOIN item i ON i.id = r.item_id
        LEFT JOIN user u1 ON u1.id = r.renter_id
        LEFT JOIN user u2 ON u2.id = r.owner_id
        ORDER BY cr.created_at DESC
    ''')
    rows = cur.fetchall()
    commissions = []
    for row in rows:
        commissions.append({
            'id': row[0], 'rental_id': row[1], 'amount': row[2], 'created_at': row[3],
            'total_amount': row[4] or 0, 'deposit_amount': row[5] or 0, 'status': row[6] or '',
            'item_name': row[7], 'renter': row[8], 'owner': row[9]
        })
    conn.close()
    return render_template('admin_commissions.html', commissions=commissions, active_nav='profile')
