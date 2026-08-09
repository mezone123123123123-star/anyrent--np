import traceback
try:
    import face_recognition
    print('face_recognition:installed')
except Exception as e:
    print('face_recognition:missing')
    traceback.print_exc()
