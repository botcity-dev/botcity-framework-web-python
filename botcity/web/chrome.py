import os
import pathlib
import tempfile
import subprocess
import re
import time
import shutil

CHROME_BINARIES = [
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/snap/bin/chromium",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
]


class ChromeLauncher:
    DEFAULT_OPTIONS = {
        "--remote-debugging-port": "0"
    }

    DEFAULT_OPTIONS_HEADLESS = {
        "--headless": "",
        "--disable-gpu": "",
        "--hide-scrollbars": "",
        "--mute-audio": ""
    }

    def __init__(self, headless, chrome_binary=None, chrome_extra_args=None):
        self._chrome_binary = chrome_binary or self.get_chrome_path()
        self._headless = headless
        if chrome_extra_args:
            extra_args = chrome_extra_args
        else:
            extra_args = self.DEFAULT_OPTIONS.copy()
            if headless:
                extra_args.update(self.DEFAULT_OPTIONS_HEADLESS)
        self._chrome_extra_args = extra_args
        self._process = None
        self._user_data_dir = None
        self._temp_dir = None
        self._devtools_port = None

    @property
    def devtools_port(self):
        return self._devtools_port

    def launch(self):
        if self._process and self._process.poll() is None:
            # Process is still alive
            return

        user_dir_param = '--user-data-dir'
        if user_dir_param in self._chrome_extra_args:
            self._user_data_dir = self._chrome_extra_args[user_dir_param]
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="botcity_")
            self._user_data_dir = self._temp_dir.name

        params = [f"{k}={v}" if v else f"{k}" for k, v in self._chrome_extra_args.items()]
        if self._temp_dir:
            params.append(f"{user_dir_param}={self._user_data_dir}")

        invocation = [self._chrome_binary] + params
        self._process = subprocess.Popen(invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.wait_for_devtools_server()

    def shutdown(self):
        if self._process and self._process.poll() is None:
            self._process.kill()

        self._process = None
        self._devtools_port = None

        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except OSError:
                shutil.rmtree(self._temp_dir.name, ignore_errors=True)
            self._temp_dir = None

    def wait_for_devtools_server(self):
        waiting_time = 50000
        start_time = time.time()
        while True:
            elapsed_time = (time.time() - start_time) * 1000
            if elapsed_time > waiting_time:
                raise RuntimeError('DevTools Server failed to start.')
            data = self._process.stderr.readline()
            data = data.replace(bytes(os.linesep, "utf-8"), b"")
            match = re.match(r"DevTools listening on ws\:\/\/.+?\:(\d+)\/devtools/browser/(.+)",
                             data.decode('utf-8')) if data else None
            if match:
                self._devtools_port = match.groups()[0]
                return
            time.sleep(0.1)

    @staticmethod
    def get_chrome_path():
        for c_path in CHROME_BINARIES:
            p = pathlib.Path(c_path)
            if not p.exists():
                continue
            if not p.is_file():
                continue
            if not os.access(p, os.X_OK):
                continue
            return c_path
        return None


if __name__ == '__main__':
    service = ChromeLauncher(headless=True)
    try:
        service.launch()
        print('service port: ', service.devtools_port)
        time.sleep(10)
    except Exception as ex:
        print('Ooops...', ex)
    finally:
        print('Will shutdown now...')
        service.shutdown()
    print('After shutdown...')
