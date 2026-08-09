import traceback
libs = ['PIL', 'imagehash']
for lib in libs:
    try:
        __import__(lib)
        print(f"{lib}:installed")
    except Exception as e:
        print(f"{lib}:missing")
        traceback.print_exc()
