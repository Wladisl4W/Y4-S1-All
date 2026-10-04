import ctypes
import os
import re
import subprocess
import time
from pathlib import Path


folder = Path(__file__).parent
screenshots = folder / 'results' / 'screenshots'
screenshots.mkdir(exist_ok=True)
env = os.environ.copy()
env['DISPLAY'] = ':99'
env['GDK_BACKEND'] = 'x11'
env['KUBECONFIG'] = str(Path.home() / '.kube' / 'config')


def capture(command, filename):
    title = 'wladisl4w@nemo: ~/uni/4/vp/2'
    terminal = subprocess.Popen(
        ['ptyxis', '-s', '--new-window', '-T', title,
         '--working-directory', str(folder), '--', 'bash', '-ic', command + '; exec bash -i'],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        window_id = None
        for _ in range(40):
            time.sleep(0.1)
            tree = subprocess.check_output(['xwininfo', '-root', '-tree'], env=env, text=True)
            match = re.search(r'(0x[0-9a-f]+) "' + re.escape(title) +
                              r'": \("ptyxis" "ptyxis"\)\s+\d+x\d+', tree)
            if match:
                window_id = int(match.group(1), 16)
                break
        if window_id is None:
            raise RuntimeError('Окно терминала не открылось')
        time.sleep(1)
        xlib = ctypes.CDLL('libX11.so.6')
        xlib.XOpenDisplay.restype = ctypes.c_void_p
        display = xlib.XOpenDisplay(b':99')
        xlib.XMoveResizeWindow(ctypes.c_void_p(display), window_id, 70, 70, 1140, 260)
        xlib.XFlush(ctypes.c_void_p(display))
        xlib.XCloseDisplay(ctypes.c_void_p(display))
        time.sleep(2)
        subprocess.run(
            ['ffmpeg', '-loglevel', 'error', '-f', 'x11grab',
             '-video_size', '1140x260', '-i', ':99+70,70', '-frames:v', '1',
             '-y', str(screenshots / filename)], check=True,
        )
    finally:
        terminal.terminate()
        terminal.wait(timeout=5)


capture('k3s kubectl -n monitoring get pods', 'monitoring-pods.png')
capture('k3s kubectl -n vp-lr2 get pods | head -12', 'app-pods.png')
for vus in (10, 50, 200):
    capture("grep -E 'checks_total|checks_succeeded|checks_failed|http_req_duration|http_req_failed|http_reqs|vus_max' results/vu%d.txt" % vus,
            'vu%d.png' % vus)
