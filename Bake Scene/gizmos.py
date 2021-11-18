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
import mathutils

from .utils import (get_size)
from .legacy import (remove_root_collection)


class BoxGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_bake_scene_box"

    # 1x1 box
    custom_verts = (
        (-0.5,  0.5, -0.5), ( 0.5,  0.5, -0.5),
        (-0.5, -0.5, -0.5), ( 0.5, -0.5, -0.5),
        (-0.5,  0.5, -0.5), (-0.5, -0.5, -0.5),
        ( 0.5,  0.5, -0.5), ( 0.5, -0.5, -0.5),

        (-0.5,  0.5,  0.5), ( 0.5,  0.5,  0.5),
        (-0.5, -0.5,  0.5), ( 0.5, -0.5,  0.5),
        (-0.5,  0.5,  0.5), (-0.5, -0.5,  0.5),
        ( 0.5,  0.5,  0.5), ( 0.5, -0.5,  0.5),

        (-0.5,  0.5, -0.5), (-0.5,  0.5,  0.5),
        ( 0.5,  0.5, -0.5), ( 0.5,  0.5,  0.5),
        (-0.5, -0.5, -0.5), (-0.5, -0.5,  0.5),
        ( 0.5, -0.5, -0.5), ( 0.5, -0.5,  0.5),
    )

    def set_dimensions(self, x, y, z):
        self.matrix[0][0] = x
        self.matrix[1][1] = y
        self.matrix[2][2] = z

    def setup(self):
        self.custom_shape = self.new_custom_shape('LINES', BoxGizmo.custom_verts)
        self.matrix = mathutils.Matrix.Identity(4)

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape, matrix=self.matrix)


class PlaneGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_bake_scene_plane"

    # 1x1 plane
    custom_verts = (
        (-0.5,  0.5, 0.0), ( 0.5,  0.5, 0.0),
        (-0.5, -0.5, 0.0), ( 0.5, -0.5, 0.0),
        (-0.5,  0.5, 0.0), (-0.5, -0.5, 0.0),
        ( 0.5,  0.5, 0.0), ( 0.5, -0.5, 0.0),
    )

    def set_dimensions(self, x, y):
        self.matrix[0][0] = x
        self.matrix[1][1] = y

    def setup(self):
        self.custom_shape = self.new_custom_shape('LINES', PlaneGizmo.custom_verts)
        self.matrix = mathutils.Matrix.Identity(4)

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape, matrix=self.matrix)


class Gizmos(bpy.types.GizmoGroup):
    bl_idname = "OBJECT_GGT_bake_scene_gizmos"
    bl_label = "Bake Scene Gizmos"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'DEPTH_3D', 'SCALE', 'SHOW_MODAL_ALL'}

    @classmethod
    def poll(cls, context):
        if context.scene:
            data = context.scene.bake_scene
            return data.show_size or (data.generate_height and data.height_mode == 'MANUAL')
        else:
            return False

    def update_gizmos(self, context):
        if context.scene:
            data = context.scene.bake_scene

            size = get_size(context, data)

            if data.show_size:
                self.size_guide.hide = False
                self.size_guide.set_dimensions(size[0], size[1])
            else:
                self.size_guide.hide = True

            if data.generate_height and data.height_mode == 'MANUAL':
                self.height_guide.hide = False
                self.height_guide.set_dimensions(size[0], size[1], data.max_height * 2.0)
            else:
                self.height_guide.hide = True

    def setup(self, context):
        box = self.gizmos.new("VIEW3D_GT_bake_scene_box")
        box.color = (0.5, 0.5, 0.5)
        box.alpha = 0.99  # This enables anti-aliasing
        box.line_width = 1
        box.use_draw_modal = True
        self.height_guide = box

        plane = self.gizmos.new("VIEW3D_GT_bake_scene_plane")
        plane.color = (1.0, 1.0, 1.0)
        plane.alpha = 0.99  # This enables anti-aliasing
        plane.line_width = 1.0
        plane.use_draw_modal = True
        self.size_guide = plane

        remove_root_collection(context)
        self.update_gizmos(context)

    def draw_prepare(self, context):
        self.update_gizmos(context)
