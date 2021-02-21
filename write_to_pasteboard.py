#!/usr/bin/python3

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

import os
import site
import sys

site.addsitedir(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party'))
from rubicon.objc import ObjCClass
from rubicon.objc import objc_const
from rubicon.objc.runtime import load_library


AppKit = load_library('AppKit')
CoreServices = load_library('CoreServices')
NSURL = ObjCClass('NSURL')
NSPasteboard = ObjCClass('NSPasteboard')
kUTTypeUTF8PlainText = objc_const(CoreServices, 'kUTTypeUTF8PlainText')


def WriteToPasteboard(text, path=None) -> None:
    pb = NSPasteboard.pasteboardWithName('mkStreamingPreview')
    pb.clearContents()
    if path:
        pb.writeObjects([text, NSURL.fileURLWithPath(path)])
    else:
        pb.setString(text, forType=kUTTypeUTF8PlainText)


if __name__ == '__main__':
    WriteToPasteboard(*sys.argv[1:])
