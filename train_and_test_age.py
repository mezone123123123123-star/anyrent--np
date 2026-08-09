"""Simple training/indexing script using perceptual image hashing.
Scans templates/static/uploads for files with 'age_template' in the filename and
attempts to extract a numeric age from the filename. Then computes phash for each
and optionally predicts age for a selfie file (first selfie_* file found).

Run: python train_and_test_age.py
"""
import os
import re
from PIL import Image
import imagehash

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, 'templates', 'static', 'uploads')


def extract_age_from_filename(fname):
    # Find numbers in filename and choose the first plausible age (1-120)
    nums = re.findall(r"(\d{1,3})", fname)
    for n in nums:
        age = int(n)
        if 1 <= age <= 120:
            return age
    return None


def build_index():
    templates = []
    for fname in os.listdir(UPLOAD_DIR):
        if 'age_template' in fname.lower():
            age = extract_age_from_filename(fname)
            path = os.path.join(UPLOAD_DIR, fname)
            try:
                phash = imagehash.phash(Image.open(path))
            except Exception as e:
                print(f"Skipping {fname}: cannot open/parse ({e})")
                continue
            templates.append({'filename': fname, 'age': age, 'phash': str(phash), 'path': path})
    return templates


def predict_from_index(selfie_path, templates):
    try:
        selfie_hash = imagehash.phash(Image.open(selfie_path))
    except Exception as e:
        print('Cannot open selfie:', e)
        return None

    candidates = []
    for t in templates:
        try:
            th = imagehash.hex_to_hash(t['phash'])
            dist = selfie_hash - th
            candidates.append((dist, t['age'], t['filename']))
        except Exception:
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    top = candidates[:3]
    total_weight = 0.0
    weighted_sum = 0.0
    for dist, age, fname in top:
        if age is None:
            continue
        w = 1.0 / (dist + 1.0)
        weighted_sum += w * age
        total_weight += w
    if total_weight == 0:
        return None
    return int(round(weighted_sum / total_weight)), top


if __name__ == '__main__':
    print('Scanning upload directory for age templates...')
    templates = build_index()
    if not templates:
        print('No age_template files found in', UPLOAD_DIR)
    else:
        print('Found templates:')
        for t in templates:
            print(' -', t['filename'], 'age=', t['age'])

    # Find a selfie to test
    selfie_path = None
    for fname in os.listdir(UPLOAD_DIR):
        if fname.lower().startswith('selfie'):
            selfie_path = os.path.join(UPLOAD_DIR, fname)
            break

    if selfie_path:
        print('\nTesting prediction on selfie:', os.path.basename(selfie_path))
        result = predict_from_index(selfie_path, templates)
        if result is None:
            print('Prediction failed or no templates with age labels available.')
        else:
            predicted_age, top = result
            print('Predicted age:', predicted_age)
            print('Top matches:')
            for d,a,f in top:
                print(f'  {f} (age={a}) distance={d}')
    else:
        print('No selfie_ file found to test prediction.')
