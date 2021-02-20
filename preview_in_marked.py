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

import sublime
import sublime_plugin

# Shim our locally-installed version of rubicon-objc
import os
import site
site.addsitedir(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party'))

from rubicon.objc import ObjCClass
from rubicon.objc import objc_const
from rubicon.objc.runtime import load_library

CoreServices = load_library('CoreServices')
NSURL = ObjCClass('NSURL')
NSPasteboard = ObjCClass('NSPasteboard')
NSWorkspace = ObjCClass('NSWorkspace')
kUTTypeUTF8PlainText = objc_const(CoreServices, 'kUTTypeUTF8PlainText')


class PreviewInMarked(sublime_plugin.ViewEventListener):
    def __init__(self, view):
        super(PreviewInMarked, self).__init__(view)
        self.pb_ = NSPasteboard.pasteboardWithName('mkStreamingPreview')
        self.setup_ = True

    def on_init(self):
        self.view.settings().add_on_change('preview_in_marked',
                                           self.on_modified)

    def on_settngs_change(self):
        self.setup_ = True
        self.on_modified()

    def on_modified(self):
        if not self.view.settings().get('preview_in_marked', False):
            return

        raw_string = self.view.substr(sublime.Region(0, self.view.size()))
        self.pb_.clearContents()

        # Marked 2 hangs for a minute on my machine after receiving a file URL,
        # so only send one when switching which file is being streamed.
        # http://support.markedapp.com/discussions/problems/161844-streaming-preview-beachballs-when-url-is-supplied
        if self.view.file_name() and self.setup_:
            base_url = NSURL.fileURLWithPath(self.view.file_name())
            self.pb_.writeObjects([raw_string, base_url])
        else:
            self.pb_.setString(raw_string, forType=kUTTypeUTF8PlainText)

        self.setup_ = False


class PreviewInMarkedCommand(sublime_plugin.TextCommand):
    def run(self, unused_edit):
        for window in sublime.windows():
            for view in window.views():
                view.settings().erase('preview_in_marked')
        self.view.settings().set('preview_in_marked', True)
