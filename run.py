from app import app
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import logging.handlers

if __name__ = "__main__":
    app.run(debug=True, port=5002)
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=truncate_logging_file, trigger="interval", seconds=60)
    scheduler.start()
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


def truncate_logging_file():
    print("IN TRUNCATE LOGGING FILE ===================================================")
    fh = logging.FileHandler('./script_log.log', "w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
