import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Item, Rental, Message, SavedItem, Review
from profile import allowed_file, allowed_video, save_message_file

marketplace_bp = Blueprint('marketplace', __name__)


def item_to_dict(item):
    owner = item.owner
    # include serialized reviews list
    reviews = []
    for r in getattr(item, 'reviews_list', []):
        reviews.append({
            'user': r.user.username if r.user else None,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat() if getattr(r, 'created_at', None) else None
        })
    return {
        'id': item.id,
        'name': item.name,
        'category': item.category,
        'type': item.type,
        'price': item.price,
        'deposit': item.deposit,
        'quantity': item.quantity,
        'location': item.location,
        'rating': item.rating,
        'reviews': item.reviews,
        'reviews_list': reviews,
        'seller': owner.username if owner else 'AnyRent',
        'verified': True,
        'image': item.image,
        'video': url_for('static', filename='uploads/' + item.video) if item.video else '',
        'description': item.description,
    }


@marketplace_bp.route('/items')
def items():
    catalog = Item.query.filter(Item.available==True, Item.is_approved==True, Item.quantity > 0).order_by(Item.created_at.desc()).all()
    items_json = json.dumps([item_to_dict(i) for i in catalog])
    saved_ids = []
    if current_user.is_authenticated:
        saved_ids = [s.item_id for s in SavedItem.query.filter_by(user_id=current_user.id).all()]
    return render_template('items.html', active_nav='items',
                           items_json=items_json, saved_ids=saved_ids)


@marketplace_bp.route('/rent', methods=['POST'])
@login_required
def rent_item():
    if not current_user.is_verified:
        flash('Verify your account first — upload your national ID from your dashboard to start renting.', 'warning')
        return redirect(url_for('profile.profile') + '#verify')

    item = Item.query.get_or_404(request.form.get('item_id'))

    if item.owner_id == current_user.id:
        flash("You can't rent your own item.", 'danger')
        return redirect(url_for('marketplace.items'))

    start = request.form.get('start_date', '')
    end = request.form.get('end_date', '')

    try:
        d1 = datetime.strptime(start, '%Y-%m-%d').date()
        d2 = datetime.strptime(end, '%Y-%m-%d').date()
        if d2 < d1:
            raise ValueError('end before start')
    except ValueError:
        flash('Choose valid rental dates (return date after start date).', 'danger')
        return redirect(url_for('marketplace.items'))

    days = max((d2 - d1).days, 1)
    total = item.price * days

    # compute deposit as 20% of total and admin commission as 15% of deposit
    deposit_amount = int(round(total * 0.20))
    admin_commission = int(round(deposit_amount * 0.15))

    rental = Rental(item_id=item.id, renter_id=current_user.id, owner_id=item.owner_id,
                    start_date=start, end_date=end, price_per_day=item.price,
                    total_amount=total, deposit_amount=deposit_amount, admin_commission=admin_commission, status='pending')
    db.session.add(rental)
    db.session.commit()

    flash(f'Rental request sent for "{item.name}" — the owner will review it. Deposit: Rs {deposit_amount} (admin commission Rs {admin_commission})', 'success')
    return redirect(url_for('profile.profile') + '#rentals')


@marketplace_bp.route('/items/<int:item_id>/message', methods=['POST'])
@login_required
def send_message(item_id):
    item = Item.query.get_or_404(item_id)
    body = request.form.get('body', '').strip()

    if not current_user.is_verified:
        flash('Verify your account first — upload your national ID from your dashboard to message owners.', 'warning')
        return redirect(url_for('profile.profile') + '#verify')

    if item.owner_id == current_user.id:
        flash('This is your own listing.', 'danger')
        return redirect(url_for('marketplace.items'))

    image = ''
    video = ''
    img_file = request.files.get('message_image')
    vid_file = request.files.get('message_video')

    if img_file and img_file.filename:
        if not allowed_file(img_file.filename):
            flash('Invalid image type. Use PNG, JPG, JPEG, GIF or WEBP.', 'danger')
            return redirect(url_for('marketplace.items'))
        image = save_message_file(img_file, 'msg_img')

    if vid_file and vid_file.filename:
        if not allowed_video(vid_file.filename):
            flash('Invalid video type. Use MP4, WebM, OGG, MOV or M4V.', 'danger')
            return redirect(url_for('marketplace.items'))
        video = save_message_file(vid_file, 'msg_vid')

    if not body and not image and not video:
        flash('Write a message or attach an image/video.', 'danger')
        return redirect(url_for('marketplace.items'))

    msg = Message(sender_id=current_user.id, receiver_id=item.owner_id,
                  item_id=item.id, body=body, image=image, video=video)
    db.session.add(msg)
    db.session.commit()

    flash(f'Message sent to @{item.owner.username}!', 'success')
    return redirect(url_for('profile.profile') + '#messages')


@marketplace_bp.route('/items/<int:item_id>/save', methods=['POST'])
@login_required
def toggle_save(item_id):
    item = Item.query.get_or_404(item_id)
    existing = SavedItem.query.filter_by(user_id=current_user.id, item_id=item.id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Removed from your saved items.', 'success')
    else:
        db.session.add(SavedItem(user_id=current_user.id, item_id=item.id))
        db.session.commit()
        flash('Saved to your list!', 'success')

    return redirect(request.referrer or url_for('marketplace.items'))


@marketplace_bp.route('/items/<int:item_id>/review', methods=['POST'])
@login_required
def submit_review(item_id):
    item = Item.query.get_or_404(item_id)
    try:
        rating = int(request.form.get('rating', 0))
    except ValueError:
        rating = 0
    comment = request.form.get('comment', '').strip()

    if rating < 1 or rating > 5:
        flash('Please provide a rating between 1 and 5.', 'danger')
        return redirect(request.referrer or url_for('marketplace.items'))

    # Prevent owner from rating their own item
    if current_user.id == item.owner_id:
        flash('You cannot rate your own item.', 'danger')
        return redirect(request.referrer or url_for('marketplace.items'))

    # Optionally, prevent duplicate reviews from same user — here allow updates by same user
    from models import Review
    existing = Review.query.filter_by(item_id=item.id, user_id=current_user.id).first()
    if existing:
        existing.rating = rating
        existing.comment = comment
    else:
        db.session.add(Review(item_id=item.id, user_id=current_user.id, rating=rating, comment=comment))

    db.session.commit()

    # Recalculate item average rating and review count
    all_reviews = Review.query.filter_by(item_id=item.id).all()
    if all_reviews:
        avg = sum(r.rating for r in all_reviews) / len(all_reviews)
        item.rating = round(avg, 1)
        item.reviews = len(all_reviews)
        db.session.commit()

    # Support AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
        return ({'status': 'ok', 'rating': item.rating, 'reviews': item.reviews}, 200)

    flash('Thank you for your feedback!', 'success')
    return redirect(request.referrer or url_for('marketplace.items'))
