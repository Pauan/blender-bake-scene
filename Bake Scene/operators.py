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

from . import bakers
from .utils import (calculate_max_height, default_settings, AddEmptyMaterial, Camera, Settings)


class CalculateMaxHeight(bpy.types.Operator):
    bl_idname = "bake_scene.calculate_max_height"
    bl_label = "Calculate max height"
    bl_description = "Sets the max height using the same algorithm as the Auto mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data = context.scene.bake_scene

        max_height = calculate_max_height(context, data)

        if max_height is None:
            self.report({'ERROR'}, "Objects are outside of baking range (" + str(data.camera_height) + "m)")
        else:
            data.max_height = max_height

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


class Bake(bpy.types.Operator):
    bl_idname = "bake_scene.bake"
    bl_label = "Bake"
    bl_description = "Bake scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data = context.scene.bake_scene

        max_height = 0

        if data.generate_height:
            if data.height_mode == 'AUTO':
                max_height = calculate_max_height(context, data)

                if max_height is None:
                    self.report({'ERROR'}, "Objects are outside of baking range (" + str(data.camera_height) + "m)")
                    return {'FINISHED'}

            elif data.height_mode == 'MANUAL':
                max_height = data.max_height

        with Settings(context) as settings, Camera(context, data.camera_height, data.size), AddEmptyMaterial(context):
            default_settings(context)

            baking = []

            # Geometry
            if data.generate_alpha:
                baking.append(lambda: bakers.bake_alpha(data, context, settings))

            if data.generate_ao:
                baking.append(lambda: bakers.bake_ao(data, context, settings))

            if data.generate_curvature:
                baking.append(lambda: bakers.bake_curvature(data, context, settings))

            if data.generate_height:
                baking.append(lambda: bakers.bake_height(data, context, settings, max_height))

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
