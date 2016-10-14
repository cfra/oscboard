#!/usr/bin/python
#
# Copyright (C) 2012 Christian Franke <nobody@nowhere.ws>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import colorsys
import urllib2
import sys

import pygtk
pygtk.require('2.0')
import gtk
import yaml
import liblo

class OSCMessage(object):
    def __init__(self, url):
        parsed = urllib2.urlparse.urlparse(url)
        self.path = parsed.path
        self.url = urllib2.urlparse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

        self.msg = liblo.Message(self.path)

    def __getattr__(self, name):
        return getattr(self.msg, name)

    def send(self):
        liblo.send(self.url, self.msg)

class OSCWindow(gtk.Window):
    def __init__(self, template):
        super(OSCWindow, self).__init__()
        self.connect("destroy", self.destroy)

        with open(template, 'r') as stream:
            setup = yaml.safe_load(stream)
        if 'title' in setup:
            self.set_title(setup['title'])

        widget, expand = self.widget_from_desc(setup['widget'])
        self.add(widget)
        self.show_all()
        self.show()

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def widget_from_desc(self, widget):
        re = True if 'expand' not in widget else widget['expand']
        if widget['type'] in ['hbox', 'vbox']:
            rw = gtk.HBox() if widget['type'] == 'hbox' else gtk.VBox()
            for desc in widget['childs']:
                child, expand = self.widget_from_desc(desc)
                if child is not None:
                    rw.pack_start(child, expand=expand)
            return rw, re

        # not containers but actual controllers
        if widget['type'] == 'vscale':
            rw = gtk.VScale()
            rw.set_range(0,255)
            rw.set_inverted(True)
            label_cont = gtk.VBox
            label_start = False
            if 'osc' in widget:
                rw.connect("value-changed", self.osc_value, widget['osc'])
        elif widget['type'] == 'hscale':
            rw = gtk.HScale()
            rw.set_range(0,255)
            rw.set_value_pos(gtk.POS_RIGHT)
            label_cont = gtk.HBox
            label_start = True
            if 'osc' in widget:
                rw.connect("value-changed", self.osc_value, widget['osc'])
        elif widget['type'] == 'colorsel':
            rw = gtk.HSV()
            label_cont = gtk.HBox
            label_start = True
            if 'osc' in widget:
                rw.connect("changed", self.osc_color, widget['osc'])
        else:
            print >>sys.stderr, "Don't know about widget '%s'" % widget['type']
            return None, None

        if 'label' in widget:
            if widget['label'] == 'below':
                label_cont = gtk.VBox
                label_start = False
            elif widget['label'] == 'above':
                label_cont = gtk.VBox
                label_start = True
            elif widget['label'] == 'left':
                label_cont = gtk.HBox
                label_start = True
            elif widget['label'] == 'right':
                label_cont = gtk.HBox
                label_start = True

        if 'name' in widget:
            container = label_cont()
            label = gtk.Label(widget['name'])
            if label_start:
                container.pack_start(label, expand=False)
                container.pack_end(rw)
            else:
                container.pack_start(rw)
                container.pack_end(label, expand=False)
            rw = container

        return rw, re

    def osc_color(self, widget, url):
        colors = colorsys.hsv_to_rgb(*widget.get_color())
        msg = OSCMessage(url)
        for color in colors:
            msg.add(int(255 * color))
        msg.send()

    def osc_value(self, widget, url):
        value = widget.get_value()
        msg = OSCMessage(url)
        msg.add(int(value))
        msg.send()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, "Usage: %s <board-config>" % sys.argv[0]
        sys.exit(1)
    osc_window = OSCWindow(sys.argv[1])
    gtk.main()
