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
import sublime
import sublime_plugin
import subprocess

from . import write_to_pasteboard

site.addsitedir(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party'))
from rubicon.objc import ObjCClass


NSURL = ObjCClass('NSURL')
NSWorkspace = ObjCClass('NSWorkspace')


class PreviewInMarked(sublime_plugin.ViewEventListener):
    def __init__(self, view):
        super(PreviewInMarked, self).__init__(view)
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
        if self.view.file_name() and self.setup_:
            # Sending an NSURL to the Pasteboard from Python freezes receiving
            # apps if we stay open, so don't. Send it from a subprocess instead.
            subprocess.run([
                write_to_pasteboard.__file__, raw_string,
                self.view.file_name()
            ])
        else:
            write_to_pasteboard.WriteToPasteboard(raw_string)

        if self.setup_:
            NSWorkspace.sharedWorkspace.openURL(
                NSURL.URLWithString(
                    'x-marked://stream?x-success=com.sublimetext.4'))
        self.setup_ = False


class PreviewInMarkedCommand(sublime_plugin.TextCommand):
    def run(self, unused_edit):
        for window in sublime.windows():
            for view in window.views():
                view.settings().erase('preview_in_marked')
        self.view.settings().set('preview_in_marked', True)
