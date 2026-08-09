import os
from datetime import date, datetime
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, AgeTemplate

try:
    import face_recognition
except ImportError:
    face_recognition = None

verification_bp = Blueprint('verification', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calculate_age(birth_date: date) -> int:
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def save_upload(file, prefix: str) -> tuple[str, str]:
    filename = secure_filename(file.filename)
    stored_name = f"{prefix}_{current_user.id}_{filename}"
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)
    file.save(file_path)
    return stored_name, file_path


from PIL import Image
import imagehash


def compare_faces(id_path: str, selfie_path: str) -> bool | None:
    # Keep existing face_recognition-based comparison for identity matching.
    if face_recognition is None:
        return None

    try:
        id_image = face_recognition.load_image_file(id_path)
        selfie_image = face_recognition.load_image_file(selfie_path)
        id_encodings = face_recognition.face_encodings(id_image)
        selfie_encodings = face_recognition.face_encodings(selfie_image)

        if not id_encodings or not selfie_encodings:
            return False

        matches = face_recognition.compare_faces([id_encodings[0]], selfie_encodings[0], tolerance=0.55)
        return bool(matches and matches[0])
    except Exception:
        return False


def get_template_file_path(template):
    return os.path.join(current_app.config['UPLOAD_FOLDER'], template.image_filename)


def predict_age_from_templates(selfie_path: str, templates):
    """
    Predict age by comparing perceptual image hashes (phash) between the selfie and labeled template photos.
    Returns integer age estimate or None.
    """
    if not templates:
        return None

    try:
        selfie_hash = imagehash.phash(Image.open(selfie_path))
    except Exception:
        return None

    candidates = []
    for template in templates:
        template_path = get_template_file_path(template)
        try:
            template_hash = imagehash.phash(Image.open(template_path))
        except Exception:
            continue
        distance = selfie_hash - template_hash
        candidates.append((distance, template.age_label))

    if not candidates:
        return None

    # Choose a weighted average of the top 3 nearest templates (lower hamming distance = closer)
    candidates.sort(key=lambda pair: pair[0])
    top = candidates[:3]
    total_weight = 0.0
    weighted_sum = 0.0
    for distance, age in top:
        weight = 1.0 / (distance + 1.0)  # avoid div by zero
        weighted_sum += weight * age
        total_weight += weight

    if total_weight == 0:
        return None

    return int(round(weighted_sum / total_weight))


@verification_bp.route('/age-templates', methods=['GET', 'POST'])
@login_required
def age_templates():
    # Age-template training feature has been disabled per request.
    # The original implementation (uploading labeled templates and using face_recognition to compare)
    # has been intentionally disabled to remove on-device training behavior.
    flash('Age-template training feature has been disabled.', 'info')
    return redirect(url_for('verification.verify_user'))


@verification_bp.route('/verification', methods=['GET', 'POST'])
@login_required
def verify_user():
    if request.method == 'POST':
        dob_str = request.form.get('date_of_birth', '').strip()
        citizenship = request.form.get('citizenship', '').strip()
        national_id = request.files.get('national_id')
        selfie = request.files.get('selfie')

        if not dob_str or not citizenship or not national_id or not selfie:
            flash('Please provide your date of birth, citizenship, national ID image, and selfie.', 'danger')
            return redirect(url_for('verification.verify_user'))

        if national_id.filename == '' or selfie.filename == '':
            flash('Please select both a national ID image and a selfie photo.', 'danger')
            return redirect(url_for('verification.verify_user'))

        if not allowed_file(national_id.filename) or not allowed_file(selfie.filename):
            flash('Invalid image type. Use PNG, JPG, JPEG, GIF or WEBP.', 'danger')
            return redirect(url_for('verification.verify_user'))

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Enter a valid date of birth using the calendar picker.', 'danger')
            return redirect(url_for('verification.verify_user'))

        id_filename, id_path = save_upload(national_id, 'nid')
        selfie_filename, selfie_path = save_upload(selfie, 'selfie')

        current_user.date_of_birth = dob
        current_user.citizenship = citizenship
        current_user.national_id_image = id_filename
        current_user.selfie_image = selfie_filename
        current_user.age_verified = calculate_age(dob) >= 18
        current_user.citizenship_verified = bool(citizenship)

        age_templates = AgeTemplate.query.filter_by(user_id=current_user.id).all()
        predicted_age = None
        if age_templates and face_recognition is not None:
            predicted_age = predict_age_from_templates(selfie_path, age_templates)
            current_user.predicted_age = predicted_age

        face_match = compare_faces(id_path, selfie_path)
        if face_match is True:
            current_user.face_verified = True
            flash('Face recognition matched your selfie with your ID photo.', 'success')
        elif face_match is False:
            current_user.face_verified = False
            flash('The selfie did not match the ID photo. Please try again or contact support.', 'danger')
        else:
            current_user.face_verified = False
            flash('Face recognition is unavailable on this server. Your photos were submitted for review.', 'warning')

        if current_user.age_verified and current_user.citizenship_verified and current_user.face_verified:
            current_user.verification_status = 'verified'
            flash('Your account is fully verified.', 'success')
        else:
            current_user.verification_status = 'pending'

        if predicted_age is not None:
            flash(f'Estimated age from your template photos: {predicted_age}', 'info')

        db.session.commit()

        session['age_verified'] = current_user.age_verified
        session['citizenship_verified'] = current_user.citizenship_verified
        session['face_verified'] = current_user.face_verified
        session['predicted_age'] = current_user.predicted_age
        session['verified'] = (current_user.age_verified and current_user.citizenship_verified
                               and current_user.face_verified)

        if not current_user.age_verified:
            flash('You must be at least 18 years old to use this service.', 'danger')

        return redirect(url_for('profile.profile'))

    return render_template('verification.html', active_nav='home', face_supported=face_recognition is not None)


@verification_bp.route('/predict-age', methods=['POST'])
@login_required
def predict_age():
    """Predict age for an uploaded selfie or the user's saved selfie using stored template phashes.
    Stores predicted_age on the user and commits to DB. Returns JSON for AJAX or redirects otherwise.
    """
    from models import AgeTemplate
    from flask import jsonify

    def ajax_response(payload, status=200):
        return jsonify(payload), status

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json

    selfie = request.files.get('selfie')
    selfie_path = None
    if selfie and selfie.filename != '':
        selfie_filename, selfie_path = save_upload(selfie, 'predict_selfie')
    elif current_user.selfie_image:
        selfie_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.selfie_image)

    if not selfie_path or not os.path.exists(selfie_path):
        msg = 'No selfie provided or found for prediction.'
        if is_ajax:
            return ajax_response({'status': 'error', 'message': msg}, 400)
        flash(msg, 'danger')
        return redirect(url_for('profile.profile'))

    try:
        selfie_hash = imagehash.phash(Image.open(selfie_path))
    except Exception:
        msg = 'Could not process selfie image.'
        if is_ajax:
            return ajax_response({'status': 'error', 'message': msg}, 400)
        flash(msg, 'danger')
        return redirect(url_for('profile.profile'))

    templates = AgeTemplate.query.filter(AgeTemplate.phash != None).all()
    candidates = []
    for t in templates:
        if not t.phash:
            continue
        try:
            th = imagehash.hex_to_hash(t.phash)
            dist = selfie_hash - th
            candidates.append((dist, t.age_label, t.image_filename))
        except Exception:
            continue

    if not candidates:
        msg = 'No indexed template photos available to predict age.'
        if is_ajax:
            return ajax_response({'status': 'error', 'message': msg}, 200)
        flash(msg, 'warning')
        return redirect(url_for('profile.profile'))

    candidates.sort(key=lambda x: x[0])
    top = candidates[:5]
    total_weight = 0.0
    weighted_sum = 0.0
    top_list = []
    for dist, age, fname in top:
        top_list.append({'distance': int(dist), 'age': age, 'filename': fname})
        if age is None:
            continue
        w = 1.0 / (dist + 1.0)
        weighted_sum += w * age
        total_weight += w

    if total_weight == 0:
        msg = 'Prediction failed due to lack of labeled templates.'
        if is_ajax:
            return ajax_response({'status': 'error', 'message': msg}, 200)
        flash(msg, 'warning')
        return redirect(url_for('profile.profile'))

    predicted_age = int(round(weighted_sum / total_weight))
    current_user.predicted_age = predicted_age
    db.session.commit()

    if is_ajax:
        return ajax_response({'status': 'ok', 'predicted_age': predicted_age, 'top': top_list}, 200)

    flash(f'Predicted age: {predicted_age}', 'info')
    return redirect(url_for('profile.profile'))
