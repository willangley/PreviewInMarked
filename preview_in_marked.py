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
import threading

from . import write_to_pasteboard

site.addsitedir(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party'))
from rubicon.objc import ObjCClass

NSURL = ObjCClass('NSURL')  # Framework: Foundation
NSWorkspace = ObjCClass(
    'NSWorkspace')  # Framework: AppKit, from write_to_pasteboard


def plugin_loaded():
    write_to_pasteboard.LaunchPasteboardWriter(pasteboard='mkStreamingPreview')


class PreviewInMarked(sublime_plugin.ViewEventListener):
    def __init__(self, view):
        super(PreviewInMarked, self).__init__(view)
        self.debounce_seconds_ = (
            sublime.load_settings('PreviewInMarked.sublime-settings').get(
                'debounce_seconds', 1.0))

        # All non-constant variables in this class are guarded by self.lock_
        self.lock_ = threading.RLock()
        self.setup_ = True
        self.update_pending_ = False
        self.timer_ = None

    def on_init(self):
        self.view.settings().add_on_change('preview_in_marked',
                                           self.handle_settings_change)

    def handle_settings_change(self):
        with self.lock_:
            self.stop_timer()
            self.setup_ = True
            self.on_modified()

    def on_modified(self):
        if not self.view.settings().get('preview_in_marked', False):
            return

        with self.lock_:
            if self.setup_:
                self.show_preview()
            else:
                self.update_pending_ = True

            self.start_timer()

    def start_timer(self):
        with self.lock_:
            self.stop_timer()
            self.timer_ = threading.Timer(self.debounce_seconds_,
                                          self.handle_timer)
            self.timer_.start()

    def handle_timer(self):
        with self.lock_:
            if not self.update_pending_:
                self.stop_timer()
                return

            self.show_preview()
            self.update_pending_ = False
            self.start_timer()

    def stop_timer(self):
        with self.lock_:
            if not self.timer_:
                return
            self.timer_.cancel()
            self.timer_ = None

    def show_preview(self):
        with self.lock_:
            raw_string = self.view.substr(sublime.Region(0, self.view.size()))
            if self.view.file_name() and self.setup_:
                write_to_pasteboard.WriteToPasteboard(raw_string,
                                                      self.view.file_name())
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
