#!/usr/bin/env python3

# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import asyncio
import cmd
import os
import pickle
import site
import subprocess
import sys
import tempfile

site.addsitedir(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party'))
from rubicon.objc import ObjCClass
from rubicon.objc import objc_const
from rubicon.objc.eventloop import EventLoopPolicy
from rubicon.objc.runtime import load_library

AppKit = load_library('AppKit')
CoreServices = load_library('CoreServices')
NSURL = ObjCClass('NSURL')  # Framework: Foundation
NSPasteboard = ObjCClass('NSPasteboard')  # Framework: AppKit
kUTTypeUTF8PlainText = objc_const(CoreServices, 'kUTTypeUTF8PlainText')

parser = argparse.ArgumentParser(
    description='write_to_pasteboard: write to the pasteboard')
parser.add_argument('-i',
                    '--interactive',
                    action='store_true',
                    help='starts an interactive prompt')
parser.add_argument('-p', '--pasteboard', help='pasteboard to write to')

args = None
loop = None
output = None
writer = None


def WriteToPasteboard(text, path=None) -> None:
    if writer:
        request = {"text": text}
        if path:
            request["path"] = path
        pickle.dump(request, writer.stdin)
        writer.stdin.flush()
        return

    print(text, path, args.pasteboard)
    pb = NSPasteboard.pasteboardWithName(
        args.pasteboard) if args.pasteboard else NSPasteboard.generalPasteboard
    pb.clearContents()
    if path:
        pb.writeObjects([text, NSURL.fileURLWithPath(path)])
    else:
        pb.setString(text, forType=kUTTypeUTF8PlainText)


def read_input():
    try:
        WriteToPasteboard(**pickle.load(sys.stdin.buffer))
    except Exception as e:
        print(e, file=sys.stderr)
        loop.stop()


def PasteboardWriter():
    global loop
    asyncio.set_event_loop_policy(EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.add_reader(sys.stdin.fileno(), read_input)
    loop.run_forever()


def LaunchPasteboardWriter(pasteboard=None):
    global output
    global writer
    output = tempfile.NamedTemporaryFile(delete=False)
    writer_args = ['python3', __file__]
    if pasteboard:
        writer_args += ['--pasteboard', pasteboard]
    writer = subprocess.Popen(writer_args,
                              stdin=subprocess.PIPE,
                              stdout=output,
                              stderr=subprocess.STDOUT)


class PasteShell(cmd.Cmd):
    intro = 'Welcome to the paste shell. Type help or ? to list commands.\n'
    prompt = '(paste) '
    path = None

    def preloop(self):
        LaunchPasteboardWriter(pasteboard=args.pasteboard)

    def do_setpath(self, arg):
        self.path = arg

    def do_clearpath(self, arg):
        self.path = None

    def do_paste(self, arg):
        'Paste data!'
        WriteToPasteboard(arg, self.path)

    def do_exit(self, arg):
        return True

    def postloop(self):
        writer.terminate()
        print("Output captured to ", output.name)


def main():
    global args
    args = parser.parse_args()
    if args.interactive:
        PasteShell().cmdloop()
    else:
        PasteboardWriter()


if __name__ == '__main__':
    main()
