from agent import app

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        app.run(port=4998, debug=True, host='0.0.0.0')
    else:
        app.run(port=4998, debug=False, host='127.0.0.1')
