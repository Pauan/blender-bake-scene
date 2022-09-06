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
from math import (radians)

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


class SphereGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_bake_scene_sphere"

    # 64-vertex circle
    custom_verts = (
        (0.0, 1.0, 0.0),
        (-0.0980171412229538, 0.9951847195625305, 0.0),
        (-0.19509032368659973, 0.9807852506637573, 0.0),
        (-0.2902846932411194, 0.9569403529167175, 0.0),
        (-0.3826834559440613, 0.9238795042037964, 0.0),
        (-0.47139671444892883, 0.8819212913513184, 0.0),
        (-0.5555702447891235, 0.8314695954322815, 0.0),
        (-0.6343932747840881, 0.7730104923248291, 0.0),
        (-0.7071067690849304, 0.7071067690849304, 0.0),
        (-0.7730104327201843, 0.6343932747840881, 0.0),
        (-0.8314695954322815, 0.5555702447891235, 0.0),
        (-0.8819212317466736, 0.4713967740535736, 0.0),
        (-0.9238795042037964, 0.3826834261417389, 0.0),
        (-0.9569403529167175, 0.2902846336364746, 0.0),
        (-0.9807852506637573, 0.19509035348892212, 0.0),
        (-0.9951847195625305, 0.0980171337723732, 0.0),
        (-1.0, -4.371138828673793e-08, 0.0),
        (-0.9951847195625305, -0.09801710397005081, 0.0),
        (-0.9807852506637573, -0.19509032368659973, 0.0),
        (-0.9569402933120728, -0.2902847230434418, 0.0),
        (-0.9238795638084412, -0.3826833963394165, 0.0),
        (-0.8819212913513184, -0.47139662504196167, 0.0),
        (-0.8314696550369263, -0.5555701851844788, 0.0),
        (-0.7730104923248291, -0.6343932747840881, 0.0),
        (-0.7071067690849304, -0.7071067690849304, 0.0),
        (-0.6343932747840881, -0.7730104923248291, 0.0),
        (-0.5555701851844788, -0.8314696550369263, 0.0),
        (-0.4713968336582184, -0.8819212317466736, 0.0),
        (-0.38268348574638367, -0.9238795042037964, 0.0),
        (-0.2902847230434418, -0.9569403529167175, 0.0),
        (-0.19509030878543854, -0.9807853102684021, 0.0),
        (-0.09801709651947021, -0.9951847195625305, 0.0),
        (8.742277657347586e-08, -1.0, 0.0),
        (0.09801702946424484, -0.9951847195625305, 0.0),
        (0.19509024918079376, -0.9807853102684021, 0.0),
        (0.290284663438797, -0.9569403529167175, 0.0),
        (0.3826834261417389, -0.9238795042037964, 0.0),
        (0.4713967740535736, -0.8819212317466736, 0.0),
        (0.5555703043937683, -0.8314695358276367, 0.0),
        (0.6343932151794434, -0.7730105519294739, 0.0),
        (0.7071067094802856, -0.7071068286895752, 0.0),
        (0.7730104327201843, -0.6343933343887329, 0.0),
        (0.8314694762229919, -0.5555704236030579, 0.0),
        (0.8819212913513184, -0.47139668464660645, 0.0),
        (0.9238795042037964, -0.38268357515335083, 0.0),
        (0.9569403529167175, -0.29028454422950745, 0.0),
        (0.9807852506637573, -0.1950903832912445, 0.0),
        (0.9951847195625305, -0.09801693260669708, 0.0),
        (1.0, 1.1924880638503055e-08, 0.0),
        (0.9951847195625305, 0.09801695495843887, 0.0),
        (0.9807852506637573, 0.1950904130935669, 0.0),
        (0.9569403529167175, 0.29028457403182983, 0.0),
        (0.9238794445991516, 0.3826836049556732, 0.0),
        (0.8819212913513184, 0.47139671444892883, 0.0),
        (0.831469714641571, 0.5555700659751892, 0.0),
        (0.7730104327201843, 0.6343933343887329, 0.0),
        (0.70710688829422, 0.7071066498756409, 0.0),
        (0.6343931555747986, 0.7730105519294739, 0.0),
        (0.5555703043937683, 0.8314695954322815, 0.0),
        (0.4713965356349945, 0.8819213509559631, 0.0),
        (0.3826834261417389, 0.9238795638084412, 0.0),
        (0.2902848422527313, 0.9569402933120728, 0.0),
        (0.19509023427963257, 0.9807853102684021, 0.0),
        (0.09801724553108215, 0.9951847195625305, 0.0),
        (0.0, 1.0, 0.0),
    )

    def set_size(self, size):
        self.matrix[0][0] = size
        self.matrix[1][1] = size
        self.matrix[2][2] = size

    def setup(self):
        self.custom_shape = self.new_custom_shape('LINE_STRIP', SphereGizmo.custom_verts)
        self.matrix = mathutils.Matrix.Identity(4)

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape, matrix=self.matrix)

        matrix = self.matrix.copy() @ mathutils.Matrix.Rotation(radians(90.0), 4, 'X')
        self.draw_custom_shape(self.custom_shape, matrix=matrix)

        matrix = self.matrix.copy() @ mathutils.Matrix.Rotation(radians(90.0), 4, 'Y')
        self.draw_custom_shape(self.custom_shape, matrix=matrix)


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

            if data.camera_mode == 'TOP':
                return data.show_size or (data.generate_height and data.height_mode == 'MANUAL')

            elif data.camera_mode == 'HDRI':
                return (data.generate_depth and data.depth_mode == 'MANUAL')

        else:
            return False

    def update_gizmos(self, context):
        if context.scene:
            data = context.scene.bake_scene

            size = get_size(context, data)

            if data.show_size and data.camera_mode == 'TOP':
                self.size_guide.hide = False
                self.size_guide.set_dimensions(size[0], size[1])
            else:
                self.size_guide.hide = True

            if data.generate_height and data.height_mode == 'MANUAL' and data.camera_mode == 'TOP':
                self.height_guide.hide = False
                self.height_guide.set_dimensions(size[0], size[1], data.max_height * 2.0)
            else:
                self.height_guide.hide = True

            if data.generate_depth and data.depth_mode == 'MANUAL' and data.camera_mode == 'HDRI':
                self.depth_guide.hide = False
                self.depth_guide.set_size(data.max_depth)
            else:
                self.depth_guide.hide = True

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

        sphere = self.gizmos.new("VIEW3D_GT_bake_scene_sphere")
        sphere.color = (0.5, 0.5, 0.5)
        sphere.alpha = 0.99  # This enables anti-aliasing
        sphere.line_width = 1.0
        sphere.use_draw_modal = True
        self.depth_guide = sphere

        self.update_gizmos(context)

    def draw_prepare(self, context):
        self.update_gizmos(context)
