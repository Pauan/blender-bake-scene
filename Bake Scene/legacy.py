# Copyright © 2021 Pauan
#
# This file is part of Bake Scene.
#
# Bake Scene is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bake Scene is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bake Scene.  If not, see <https://www.gnu.org/licenses/>.

import bpy


def remove_object(object):
    data = object.data

    bpy.data.objects.remove(object)

    if data is not None:
        bpy.data.meshes.remove(data)


def remove_collection_recursive(collection):
    for child in collection.objects:
        remove_object(child)

    for sub in collection.children:
        remove_collection_recursive(sub)

    assert len(collection.children) == 0 and len(collection.objects) == 0

    bpy.data.collections.remove(collection)


def remove_root_collection(context):
    if context.scene:
        data = context.scene.bake_scene

        if data.collection:
            remove_collection_recursive(data.collection)

        data.collection = None
        data.height_bounds = None
