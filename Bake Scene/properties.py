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
from bpy.props import (IntProperty, FloatProperty, PointerProperty, EnumProperty, BoolProperty)


# This causes the gizmo to update when the property is changed
def update_noop(self, context):
    pass


class Scene(bpy.types.PropertyGroup):
    # TODO deprecate and remove these
    collection: PointerProperty(type=bpy.types.Collection)
    height_bounds: PointerProperty(type=bpy.types.Object)

    camera_mode: EnumProperty(
        name="Type",
        description="Type of baking",
        default='TOP',
        update=update_noop,
        options=set(),
        items=(('TOP', "Flat", "Bakes the scene as an orthographic rectangle. Can be used to create trimsheets, decals, or hair cards"),
               ('HDRI', "HDRI", "Bakes the entire scene as an equirectangular HDRI"))
    )

    camera_height: FloatProperty(
        name="Camera Height",
        description="Height of the camera",
        default=50,
        min=0,
        subtype='DISTANCE',
        unit='LENGTH',
        options=set(),
    )

    size: FloatProperty(
        name="Size",
        description="Width / height of the scene",
        default=2,
        min=0,
        step=1,
        precision=5,
        subtype='DISTANCE',
        unit='LENGTH',
        options=set(),
        update=update_noop,
    )

    show_size: BoolProperty(
        name="Show Size",
        description="Whether the size is visible or not",
        default=False,
        options=set(),
        update=update_noop,
    )

    height_mode: EnumProperty(
        name="Mode",
        description="Calculate max height automatically or manually",
        default='AUTO',
        update=update_noop,
        options=set(),
        items=(('AUTO', "Auto", ""),
               ('MANUAL', "Manual", ""))
    )

    max_height: FloatProperty(
        name="Max",
        description="Maximum height for height texture",
        default=1,
        min=0,
        step=1,
        precision=5,
        subtype='DISTANCE',
        unit='LENGTH',
        options=set(),
        update=update_noop,
    )

    depth_mode: EnumProperty(
        name="Mode",
        description="Calculate max depth automatically or manually",
        default='AUTO',
        update=update_noop,
        options=set(),
        items=(('AUTO', "Auto", ""),
               ('MANUAL', "Manual", ""))
    )

    max_depth: FloatProperty(
        name="Max",
        description="Maximum depth for depth texture",
        default=1,
        min=0,
        step=1,
        precision=5,
        subtype='DISTANCE',
        unit='LENGTH',
        options=set(),
        update=update_noop,
    )

    curvature_contrast: FloatProperty(
        name="Contrast",
        description="Controls the amount of contrast in the curvature map",
        default=1,
        min=0,
        step=1,
        precision=5,
        subtype='UNSIGNED',
        unit='NONE',
        options=set(),
    )

    generate_render: BoolProperty(
        name="Render",
        description="Generate final render texture for scene",
        default=False,
        options=set(),
    )

    generate_alpha: BoolProperty(
        name="Alpha",
        description="Generate alpha texture",
        default=True,
        options=set(),
    )

    generate_ao: BoolProperty(
        name="AO",
        description="Generate ambient occlusion texture",
        default=True,
        options=set(),
    )

    generate_color: BoolProperty(
        name="Color",
        description="Generate base color texture",
        default=False,
        options=set(),
    )

    generate_curvature: BoolProperty(
        name="Curvature",
        description="Generate curvature texture",
        default=True,
        options=set(),
    )

    generate_emission: BoolProperty(
        name="Emission",
        description="Generate emission texture",
        default=False,
        options=set(),
    )

    generate_hair_random: BoolProperty(
        name="Hair Random",
        description="Generate hair random texture",
        default=False,
        options=set(),
    )

    generate_hair_root: BoolProperty(
        name="Hair Root",
        description="Generate hair root texture",
        default=False,
        options=set(),
    )

    generate_height: BoolProperty(
        name="Height",
        description="Generate height texture",
        default=True,
        options=set(),
        update=update_noop,
    )

    generate_depth: BoolProperty(
        name="Depth",
        description="Generate depth texture",
        default=True,
        options=set(),
        update=update_noop,
    )

    generate_metallic: BoolProperty(
        name="Metallic",
        description="Generate metallic texture",
        default=False,
        options=set(),
    )

    generate_normal: BoolProperty(
        name="Normal",
        description="Generate normal map texture",
        default=True,
        options=set(),
    )

    generate_roughness: BoolProperty(
        name="Roughness",
        description="Generate roughness texture",
        default=False,
        options=set(),
    )

    generate_object_random: BoolProperty(
        name="Object Random",
        description="Generate object random texture",
        default=False,
        options=set(),
    )

    generate_object_index: BoolProperty(
        name="Object Index",
        description="Generate object index texture",
        default=False,
        options=set(),
    )

    generate_object_index_max: IntProperty(
        name="Max",
        description="Maximum object index",
        default=1,
        min=0,
        step=1,
        subtype='UNSIGNED',
        options=set(),
    )

    generate_material_index: BoolProperty(
        name="Material Index",
        description="Generate material index texture",
        default=False,
        options=set(),
    )

    generate_material_index_max: IntProperty(
        name="Max",
        description="Maximum material index",
        default=1,
        min=0,
        step=1,
        subtype='UNSIGNED',
        options=set(),
    )

    generate_vertex_color: BoolProperty(
        name="Vertex Color",
        description="Generate vertex color texture",
        default=False,
        options=set(),
    )

    @classmethod
    def register(cls):
        bpy.types.Scene.bake_scene = PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.bake_scene
