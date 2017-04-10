__version__ = "0.7a1"

def main(filepath=None):
    print('init main')
    from .launch import main
    main(filepath=filepath)
