#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import socket
import SimpleHTTPServer
import SocketServer
import time
from threading import Thread

from flask import Flask, render_template, request, jsonify, redirect, url_for

from xcode_imagecleantool import XcodeImageCleanTool

app = Flask(__name__)
search_path = ""
ignore_path = ""
images = []
httpd = None
port = ""


class _InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class _ImageModel:
    location = ''
    paths = []

    def __init__(self, location, paths=None):
        if isinstance(location, unicode):
            self.location = '"%s"' % location
        else:
            raise TypeError('%s is not a string' % location)

        if paths is not None:
            if isinstance(paths, list):
                self.paths = paths
            else:
                raise TypeError('%s is not a list' % paths)
        else:
            self.paths = [location]
        self.paths = ','.join(self.paths)


@app.route('/')
def homepage():
    # TODO:refresh
    return render_template('main.html', search_path=search_path, ignore_path=ignore_path, images=images)


@app.route('/searchRepeatImages')
def search_repeat_images():
    def find_repeat_images(searchpath, ignorepath):
        tool = XcodeImageCleanTool(searchpath)
        repeat_images = tool.find_repeat_images(ignorepath)
        repeat_images = map(
            lambda x: _ImageModel(location=x.replace(searchpath, 'http://127.0.0.1:' + str(port)), paths=[x]),
            repeat_images)

        global search_path
        global ignore_path
        global images
        search_path = searchpath
        ignore_path = ignorepathstring
        images = repeat_images

    projectpath = request.args.get('projectPath')
    ignorepathstring = request.args.get('ignorePaths')
    ignorepaths = get_ignore_paths(ignorepathstring)

    if projectpath:
        if httpd is not None:
            find_repeat_images(projectpath, ignorepath=ignorepaths)
            return redirect_to_homepage('没有重复图片')
        else:
            try:
                thread = Thread(target=create_http_server, args=[projectpath])
                thread.start()
                time.sleep(2)

                find_repeat_images(projectpath, ignorepath=ignorepaths)
                return redirect_to_homepage('没有重复图片')
            except Exception, e:
                raise _InvalidUsage(e.message, status_code=400)
    else:
        raise _InvalidUsage('please enter a search path', status_code=400)


@app.route('/searchSimilarImages')
def search_similar_images():
    def find_similar_images(searchpath, ignorepath):
        tool = XcodeImageCleanTool(searchpath)
        similar_images_dic = tool.find_similar_images(ignorepath).values()
        similar_images = []
        for item_array in similar_images_dic:
            similar_images.extend(item_array[0].values())
        similar_images = map(
            lambda x: _ImageModel(location=x[0].replace(searchpath, 'http://127.0.0.1:' + str(port)), paths=x),
            similar_images)

        global search_path
        global ignore_path
        global images
        search_path = searchpath
        ignore_path = ignorepathstring
        images = similar_images

    projectpath = request.args.get('projectPath')
    ignorepathstring = request.args.get('ignorePaths')
    ignorepaths = get_ignore_paths(ignorepathstring)

    if projectpath:
        if httpd is not None:
            find_similar_images(projectpath, ignorepath=ignorepaths)
            return redirect_to_homepage('没有相似图片')
        else:
            try:
                thread = Thread(target=create_http_server, args=[projectpath])
                thread.start()
                time.sleep(2)

                find_similar_images(projectpath, ignorepath=ignorepaths)
                return redirect_to_homepage('没有相似图片')
            except Exception, e:
                raise _InvalidUsage(e.message, status_code=400)
    else:
        raise _InvalidUsage('please enter a search path', status_code=400)


@app.route('/searchUnusedImages')
def search_unused_images():
    def find_unused_images(searchpath, ignorepath):
        tool = XcodeImageCleanTool(searchpath)
        unused_images = tool.find_unused_images(ignorepath)
        unused_images = map(
            lambda x: _ImageModel(location=x.replace(searchpath, 'http://127.0.0.1:' + str(port)), paths=[x]),
            unused_images)

        global search_path
        global ignore_path
        global images
        search_path = searchpath
        ignore_path = ignorepathstring
        images = unused_images

    projectpath = request.args.get('projectPath')
    ignorepathstring = request.args.get('ignorePaths')
    ignorepaths = get_ignore_paths(ignorepathstring)

    if projectpath:
        if httpd is not None:
            find_unused_images(projectpath, ignorepath=ignorepaths)
            return redirect_to_homepage('没有未使用的图片')
        else:
            try:
                thread = Thread(target=create_http_server, args=[projectpath])
                thread.start()
                time.sleep(2)

                find_unused_images(projectpath, ignorepath=ignorepaths)
                return redirect_to_homepage('没有未使用的图片')
            except Exception, e:
                raise _InvalidUsage(e.message, status_code=400)
    else:
        raise _InvalidUsage('please enter a search path', status_code=400)


@app.route('/deleteImages', methods=['POST'])
def delete_images():
    index = map(lambda x: int(x), request.form.getlist('index[]'))
    delete_image_paths = []
    delete_image = []
    for item in index:
        if item < len(images):
            delete_image_paths.extend(images[item].paths.split(','))
            delete_image.append(images[item])
    for item in delete_image_paths:
        os.remove(item)
    for item in delete_image:
        images.remove(item)
    return '删除成功'


@app.errorhandler(_InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.listen(1)
    available_port = s.getsockname()[1]
    s.close()
    return available_port


def create_http_server(directory):
    try:
        global httpd
        if httpd is None:
            global port
            port = get_open_port()
            httpd = SocketServer.TCPServer(('', port), SimpleHTTPServer.SimpleHTTPRequestHandler)
            print 'Serving on port', port
            current_dir = os.getcwd()
            os.chdir(directory)
            httpd.serve_forever()
            os.chdir(current_dir)
    except SocketServer.socket.error as exc:
        if exc.args[0] != 48:
            raise
        print 'Port', port, 'already in use'


def get_ignore_paths(ignorepathstring):
    ignorepaths = []
    if ignorepathstring != '':
        if ',' in ignorepathstring:
            ignorepaths = ignorepathstring.split(',')
        else:
            ignorepaths.append(ignorepathstring)
    return ignorepaths


def redirect_to_homepage(hint):
    if images:
        return redirect(url_for('homepage'))
    else:
        raise _InvalidUsage(hint, status_code=204)


if __name__ == '__main__':
    app.run(debug=True)
