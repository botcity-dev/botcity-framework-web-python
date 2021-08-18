import shutil


def cleanup_temp_dir(temp_dir):
    if temp_dir:
        try:
            temp_dir.cleanup()
        except OSError:
            shutil.rmtree(temp_dir.name, ignore_errors=True)
