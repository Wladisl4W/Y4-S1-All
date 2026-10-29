"""Capture genuine Ptyxis windows with visible, executed commands."""

import ctypes
import os
import re
import subprocess
import sys
import time
from pathlib import Path

os.environ['DISPLAY'] = ':99'
os.environ['GDK_BACKEND'] = 'x11'
folder = Path(__file__).parent
screenshots = folder / 'screenshots'
screenshots.mkdir(exist_ok=True)
env = os.environ.copy()
env['DISPLAY'] = ':99'
env['GDK_BACKEND'] = 'x11'
env['KUBECONFIG'] = str(Path.home() / '.kube/config')
env['PROMPT_COMMAND'] = 'printf "\\033[?25l"'


def type_command(command):
    display = ctypes.CDLL('libX11.so.6')
    xtest = ctypes.CDLL('libXtst.so.6')
    display.XOpenDisplay.restype = ctypes.c_void_p
    display.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    display.XStringToKeysym.argtypes = [ctypes.c_char_p]
    display.XStringToKeysym.restype = ctypes.c_ulong
    xtest.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    display.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    connection = display.XOpenDisplay(b':99')
    def key(name, down):
        sym = display.XStringToKeysym(name.encode())
        code = display.XKeysymToKeycode(connection, sym)
        xtest.XTestFakeKeyEvent(connection, code, int(down), 0)
        display.XSync(ctypes.c_void_p(connection), 0)
        time.sleep(0.05)
    for character in command:
        name = {' ': 'space', '/': 'slash', '-': 'minus', '.': 'period'}.get(character, character)
        key(name, True)
        key(name, False)
    key('Return', True)
    key('Return', False)
    display.XCloseDisplay(ctypes.c_void_p(connection))
    time.sleep(3 if command.startswith('k3s') else 0.8)


def capture(filename, command, height=320):
    terminal = subprocess.Popen(
        ['ptyxis', '-s', '--new-window', '-d', str(folder)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        window_id = None
        for _ in range(50):
            time.sleep(0.1)
            tree = subprocess.check_output(['xwininfo', '-root', '-tree'], env=env, text=True)
            match = re.search(r'(0x[0-9a-f]+) "wladisl4w@nemo: ~/uni/4/vp/4"', tree)
            if match:
                window_id = int(match.group(1), 16)
                break
        if window_id is None:
            raise RuntimeError('Окно Ptyxis не открылось')
        xlib = ctypes.CDLL('libX11.so.6')
        xlib.XOpenDisplay.restype = ctypes.c_void_p
        connection = xlib.XOpenDisplay(b':99')
        xlib.XMoveResizeWindow(ctypes.c_void_p(connection), window_id, 0, 0, 1280, 570)
        xlib.XFlush(ctypes.c_void_p(connection))
        xlib.XCloseDisplay(ctypes.c_void_p(connection))
        time.sleep(0.8)
        type_command(command)
        subprocess.run(
            ['ffmpeg', '-loglevel', 'error', '-f', 'x11grab', '-draw_mouse', '0',
             '-video_size', f'1280x{height}', '-i', ':99+0,0', '-frames:v', '1',
             '-y', str(screenshots / filename)], check=True,
        )
    finally:
        terminal.terminate()
        terminal.wait(timeout=5)


if __name__ == '__main__':
    display = subprocess.Popen(
        ['Xvfb', ':99', '-screen', '0', '1280x570x24', '-nolisten', 'tcp'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    manager = None
    try:
        time.sleep(1)
        if display.poll() is not None:
            raise RuntimeError('Не удалось открыть виртуальный экран :99')
        manager = subprocess.Popen(['openbox'], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        capture('cluster-pods.png', 'k3s kubectl get pods -n vp-lr4')
        for replicas in (1, 2, 3):
            capture(f'r{replicas}-pods.png', f'cat results/r{replicas}-pods.txt', 190)
            original = (folder / 'results' / f'r{replicas}-rate100.txt').read_text()
            keys = ('http_req_duration', 'http_req_failed', 'http_reqs',
                    'dropped_iterations', 'checks_total', 'checks_succeeded', 'checks_failed')
            excerpt = [line for line in original.splitlines()
                       if any(key in line for key in keys)]
            (folder / 'results' / f'r{replicas}-rate100-summary.txt').write_text('\n'.join(excerpt) + '\n')
            capture(f'r{replicas}-rate100.png', f'cat results/r{replicas}-rate100-summary.txt')
    finally:
        if manager is not None:
            manager.terminate()
            manager.wait(timeout=5)
        display.terminate()
        display.wait(timeout=5)
