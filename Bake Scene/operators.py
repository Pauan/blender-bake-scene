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

import time
import bpy
from math import radians

from . import bakers
from .utils import (calculate_max_height, calculate_max_depth, default_settings, AddEmptyMaterial, Camera, Settings)


class HeightOperator:
    def height_error(self, data):
        self.report({'ERROR'}, "Objects are outside of baking range (" + str(round(data.camera_height)) + "m)")


class CalculateMaxHeight(bpy.types.Operator, HeightOperator):
    bl_idname = "bake_scene.calculate_max_height"
    bl_label = "Calculate max height"
    bl_description = "Sets the max height using the same algorithm as the Auto mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data = context.scene.bake_scene

        max_height = calculate_max_height(context, data)

        if max_height is None:
            self.height_error(data)
        else:
            data.max_height = max_height

        return {'FINISHED'}


class CalculateMaxDepth(bpy.types.Operator):
    bl_idname = "bake_scene.calculate_max_depth"
    bl_label = "Calculate max depth"
    bl_description = "Sets the max depth using the same algorithm as the Auto mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data = context.scene.bake_scene

        data.max_depth = calculate_max_depth(context)

        return {'FINISHED'}


class ShowSize(bpy.types.Operator):
    bl_idname = "bake_scene.show_size"
    bl_label = "Show size"
    bl_description = "Shows the bounding box for the size"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        data = context.scene.bake_scene
        data.show_size = True
        return {'FINISHED'}


class HideSize(bpy.types.Operator):
    bl_idname = "bake_scene.hide_size"
    bl_label = "Hide size"
    bl_description = "Hides the bounding box for the size"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        data = context.scene.bake_scene
        data.show_size = False
        return {'FINISHED'}


class Bake(bpy.types.Operator, HeightOperator):
    bl_idname = "bake_scene.bake"
    bl_label = "Bake"
    bl_description = "Bake scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data = context.scene.bake_scene

        max_height = 0
        max_depth = 0

        if data.generate_height and data.camera_mode == 'TOP':
            if data.height_mode == 'AUTO':
                # TODO maybe it should always do this check, in order to check for out of camera bounds
                max_height = calculate_max_height(context, data)

                if max_height is None:
                    self.height_error(data)
                    return {'FINISHED'}

            elif data.height_mode == 'MANUAL':
                max_height = data.max_height


        if data.generate_depth and data.camera_mode == 'HDRI':
            if data.depth_mode == 'AUTO':
                max_depth = calculate_max_depth(context)

            elif data.depth_mode == 'MANUAL':
                max_depth = data.max_depth


        with Settings(context) as settings, Camera(context) as camera, AddEmptyMaterial(context):
            if data.camera_mode == 'TOP':
                camera.data.type = 'ORTHO'
                camera.data.ortho_scale = data.size
                camera.data.clip_end = data.camera_height * 2
                camera.location = (0.0, 0.0, data.camera_height)

            elif data.camera_mode == 'HDRI':
                camera.data.type = 'PANO'
                camera.data.cycles.panorama_type = 'EQUIRECTANGULAR'
                camera.location = (0.0, 0.0, 0.0)
                camera.rotation_euler = (radians(90.0), 0.0, 0.0)

            baking = []

            # This must come first, because it must bake with the user's settings
            if data.generate_render:
                baking.append(lambda: bakers.bake_render(data, context, settings))

            # Geometry
            if data.generate_alpha:
                baking.append(lambda: bakers.bake_alpha(data, context, settings))

            if data.generate_ao:
                baking.append(lambda: bakers.bake_ao(data, context, settings))

            if data.generate_curvature:
                baking.append(lambda: bakers.bake_curvature(data, context, settings))

            if data.generate_height and data.camera_mode == 'TOP':
                baking.append(lambda: bakers.bake_height(data, context, settings, max_height))

            if data.generate_depth and data.camera_mode == 'HDRI':
                baking.append(lambda: bakers.bake_depth(data, context, settings, max_depth))

            if data.generate_normal:
                baking.append(lambda: bakers.bake_normal(data, context, settings))

            # Material
            if data.generate_color:
                baking.append(lambda: bakers.bake_color(data, context, settings))

            if data.generate_emission:
                baking.append(lambda: bakers.bake_emission(data, context, settings))

            if data.generate_metallic:
                baking.append(lambda: bakers.bake_metallic(data, context, settings))

            if data.generate_roughness:
                baking.append(lambda: bakers.bake_roughness(data, context, settings))

            if data.generate_vertex_color:
                baking.append(lambda: bakers.bake_vertex_color(data, context, settings))

            # Masking
            if data.generate_material_index:
                baking.append(lambda: bakers.bake_material_index(data, context, settings))

            if data.generate_object_index:
                baking.append(lambda: bakers.bake_object_index(data, context, settings))

            if data.generate_object_random:
                baking.append(lambda: bakers.bake_object_random(data, context, settings))

            # Hair
            if data.generate_hair_random:
                baking.append(lambda: bakers.bake_hair_random(data, context, settings))

            if data.generate_hair_root:
                baking.append(lambda: bakers.bake_hair_root(data, context, settings))

            # Bake all the textures
            context.window_manager.progress_begin(0, len(baking))
            context.window_manager.progress_update(0)

            start = time.time()

            for (index, f) in enumerate(baking, start=1):
                f()
                context.window_manager.progress_update(index)

            context.window_manager.progress_end()

            duration = time.time() - start
            self.report({'INFO'}, "Finished baking all textures (" + str(round(duration, 2)) + " seconds)")

        return {'FINISHED'}
