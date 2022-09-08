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


class TexturesScenePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bake_scene_textures_scene"
    bl_label = "Scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = "DATA_PT_bake_scene_textures"
    bl_order = 0
    bl_options = set()

    def draw(self, context):
        data = context.scene.bake_scene
        layout = self.layout

        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "generate_render")


class TexturesGeometryPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bake_scene_textures_geometry"
    bl_label = "Geometry"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = "DATA_PT_bake_scene_textures"
    bl_order = 1
    bl_options = set()

    def draw(self, context):
        data = context.scene.bake_scene
        layout = self.layout

        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "generate_alpha")

        col = flow.column()
        col.prop(data, "generate_ao")

        col = flow.column()
        col.prop(data, "generate_normal")

        flow.separator()

        col = flow.column()
        col.prop(data, "generate_curvature")
        col.prop(data, "curvature_contrast")

        flow.separator()

        if data.camera_mode == 'TOP':
            col = flow.column()
            col.prop(data, "generate_height")

            row = col.row()
            row.enabled = data.generate_height
            row.prop(data, "height_mode", expand=True)

            if data.height_mode == 'MANUAL':
                row = col.row()
                row.enabled = data.generate_height
                row.prop(data, "max_height")
                row.operator("bake_scene.calculate_max_height", text="", icon='PIVOT_BOUNDBOX')

        elif data.camera_mode == 'HDRI':
            col = flow.column()
            col.prop(data, "generate_depth")

            row = col.row()
            row.enabled = data.generate_depth
            row.prop(data, "depth_mode", expand=True)

            if data.depth_mode == 'MANUAL':
                row = col.row()
                row.enabled = data.generate_depth
                row.prop(data, "max_depth")
                row.operator("bake_scene.calculate_max_depth", text="", icon='PIVOT_BOUNDBOX')


class TexturesMaterialPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bake_scene_textures_material"
    bl_label = "Material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = "DATA_PT_bake_scene_textures"
    bl_order = 2
    bl_options = set()

    def draw(self, context):
        data = context.scene.bake_scene
        layout = self.layout

        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "generate_color")

        col = flow.column()
        col.prop(data, "generate_emission")

        col = flow.column()
        col.prop(data, "generate_metallic")

        col = flow.column()
        col.prop(data, "generate_roughness")

        col = flow.column()
        col.prop(data, "generate_vertex_color")


class TexturesMaskingPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bake_scene_textures_masking"
    bl_label = "Masking"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = "DATA_PT_bake_scene_textures"
    bl_order = 3
    bl_options = set()

    def draw(self, context):
        data = context.scene.bake_scene
        layout = self.layout

        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "generate_object_random")

        flow.separator()

        col = flow.column()
        col.prop(data, "generate_object_index")

        col = flow.column()
        col.enabled = data.generate_object_index
        col.prop(data, "generate_object_index_max")

        flow.separator()

        col = flow.column()
        col.prop(data, "generate_material_index")

        col = flow.column()
        col.enabled = data.generate_material_index
        col.prop(data, "generate_material_index_max")


class TexturesHairPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bake_scene_textures_hair"
    bl_label = "Hair"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = "DATA_PT_bake_scene_textures"
    bl_order = 4
    bl_options = set()

    def draw(self, context):
        data = context.scene.bake_scene
        layout = self.layout

        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "generate_hair_random")

        col = flow.column()
        col.prop(data, "generate_hair_root")


class TexturesPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bake_scene_textures"
    bl_label = "Textures"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_parent_id = "DATA_PT_bake_scene"
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass


class BakePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bake_scene"
    bl_label = "Bake Scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_options = set()

    def draw(self, context):
        data = context.scene.bake_scene
        layout = self.layout

        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()

        row = col.row()
        row.alignment = 'EXPAND'
        row.operator("bake_scene.bake", icon='RENDER_STILL')

        flow.separator()

        row = flow.row()
        row.prop(data, "camera_mode")

        if data.camera_mode == 'TOP':
            row = flow.row()
            row.prop(data, "size")

            if data.show_size:
                row.operator("bake_scene.hide_size", text="", icon='HIDE_OFF')
            else:
                row.operator("bake_scene.show_size", text="", icon='HIDE_ON')
