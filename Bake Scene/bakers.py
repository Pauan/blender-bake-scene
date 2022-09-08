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

from .utils import (
    antialias_on, antialias_off, view_transform_raw, view_transform_color, filename,
    default_settings, render_engine, node_group_output, render_with_input, NodeGroup,
    ReplaceMaterials, CompositorNodeGroup,
)


def bake_render(data, context, settings):
    context.scene.render.filepath = filename(data, settings, "render")
    bpy.ops.render.render(write_still=True)


def normal_node_group(tree):
    inputs = tree.nodes.new('NodeGroupInput')

    normalize = tree.nodes.new('ShaderNodeVectorMath')
    normalize.operation = 'NORMALIZE'

    transform = tree.nodes.new('ShaderNodeVectorTransform')
    transform.vector_type = 'NORMAL'
    transform.convert_from = 'WORLD'
    transform.convert_to = 'CAMERA'

    math = tree.nodes.new('ShaderNodeVectorMath')
    math.operation = 'MULTIPLY_ADD'
    math.inputs[1].default_value[0] = 0.5
    math.inputs[1].default_value[1] = 0.5
    math.inputs[1].default_value[2] = -0.5
    math.inputs[2].default_value[0] = 0.5
    math.inputs[2].default_value[1] = 0.5
    math.inputs[2].default_value[2] = 0.5

    emission = tree.nodes.new('ShaderNodeEmission')

    tree.links.new(inputs.outputs["Normal"], normalize.inputs["Vector"])
    tree.links.new(normalize.outputs["Vector"], transform.inputs["Vector"])
    tree.links.new(transform.outputs["Vector"], math.inputs["Vector"])
    tree.links.new(math.outputs["Vector"], emission.inputs["Color"])

    node_group_output(tree, inputs, emission.outputs["Emission"])


def bake_normal(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "normal")
    context.scene.render.image_settings.color_mode = 'RGB'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0.5, 0.5, 1)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Normal") as tree:
        normal_node_group(tree)

        with ReplaceMaterials(context, "__Bake_Normal"):
            bpy.ops.render.render(write_still=True)


def bake_ao(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "ao")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (1, 1, 1)

    context.scene.eevee.use_gtao = True
    context.scene.eevee.use_overscan = True
    context.scene.eevee.overscan_size = 10
    context.scene.eevee.gtao_distance = 0.2
    context.scene.eevee.gtao_factor = 1
    context.scene.eevee.gtao_quality = 0.25
    context.scene.eevee.use_gtao_bent_normals = True
    context.scene.eevee.use_gtao_bounce = False

    with NodeGroup("__Bake_AO") as tree:
        inputs = tree.nodes.new('NodeGroupInput')

        ao = tree.nodes.new('ShaderNodeAmbientOcclusion')

        if data.camera_mode == 'TOP':
            ao.samples = 128
        elif data.camera_mode == 'HDRI':
            ao.samples = 16

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(inputs.outputs["Normal"], ao.inputs["Normal"])
        tree.links.new(ao.outputs["AO"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_AO"):
            bpy.ops.render.render(write_still=True)


def bake_curvature(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "curvature")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0.5, 0.5, 1)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Curvature") as tree:
        normal_node_group(tree)

        with ReplaceMaterials(context, "__Bake_Curvature"):
            with CompositorNodeGroup(context.scene, "__Composite_Curvature") as tree:
                inputs = tree.nodes.new('NodeGroupInput')

                x_add = tree.nodes.new('CompositorNodeTransform')
                x_add.filter_type = 'BICUBIC'
                x_add.inputs[1].default_value = 1.0
                x_add.inputs[4].default_value = 1.0000001 # This fixes the 1-pixel border around the image

                x_sub = tree.nodes.new('CompositorNodeTransform')
                x_sub.filter_type = 'BICUBIC'
                x_sub.inputs[1].default_value = -1.0
                x_sub.inputs[4].default_value = 1.0000001 # This fixes the 1-pixel border around the image

                y_add = tree.nodes.new('CompositorNodeTransform')
                y_add.filter_type = 'BICUBIC'
                y_add.inputs[2].default_value = 1.0
                y_add.inputs[4].default_value = 1.0000001 # This fixes the 1-pixel border around the image

                y_sub = tree.nodes.new('CompositorNodeTransform')
                y_sub.filter_type = 'BICUBIC'
                y_sub.inputs[2].default_value = -1.0
                y_sub.inputs[4].default_value = 1.0000001 # This fixes the 1-pixel border around the image

                x_add_sep = tree.nodes.new('CompositorNodeSepRGBA')
                x_sub_sep = tree.nodes.new('CompositorNodeSepRGBA')
                y_add_sep = tree.nodes.new('CompositorNodeSepRGBA')
                y_sub_sep = tree.nodes.new('CompositorNodeSepRGBA')

                x_diff = tree.nodes.new('CompositorNodeMath')
                x_diff.operation = 'SUBTRACT'

                y_diff = tree.nodes.new('CompositorNodeMath')
                y_diff.operation = 'SUBTRACT'

                combine = tree.nodes.new('CompositorNodeMath')
                combine.operation = 'ADD'

                multiply = tree.nodes.new('CompositorNodeMath')
                multiply.operation = 'MULTIPLY'
                multiply.inputs[1].default_value = data.curvature_contrast

                normalize = tree.nodes.new('CompositorNodeMath')
                normalize.operation = 'SUBTRACT'
                normalize.use_clamp = True
                normalize.inputs[0].default_value = 0.5

                outputs = tree.nodes.new('CompositorNodeComposite')
                outputs.select = True

                tree.links.new(inputs.outputs["Image"], x_add.inputs["Image"])
                tree.links.new(inputs.outputs["Image"], x_sub.inputs["Image"])
                tree.links.new(inputs.outputs["Image"], y_add.inputs["Image"])
                tree.links.new(inputs.outputs["Image"], y_sub.inputs["Image"])
                tree.links.new(x_add.outputs["Image"], x_add_sep.inputs["Image"])
                tree.links.new(x_sub.outputs["Image"], x_sub_sep.inputs["Image"])
                tree.links.new(y_add.outputs["Image"], y_add_sep.inputs["Image"])
                tree.links.new(y_sub.outputs["Image"], y_sub_sep.inputs["Image"])
                tree.links.new(x_add_sep.outputs["R"], x_diff.inputs[0])
                tree.links.new(x_sub_sep.outputs["R"], x_diff.inputs[1])
                tree.links.new(y_add_sep.outputs["G"], y_diff.inputs[0])
                tree.links.new(y_sub_sep.outputs["G"], y_diff.inputs[1])
                tree.links.new(x_diff.outputs["Value"], combine.inputs[0])
                tree.links.new(y_diff.outputs["Value"], combine.inputs[1])
                tree.links.new(combine.outputs["Value"], multiply.inputs[0])
                tree.links.new(multiply.outputs["Value"], normalize.inputs[1])
                tree.links.new(normalize.outputs["Value"], outputs.inputs["Image"])

                bpy.ops.render.render(write_still=True)


def bake_height(data, context, settings, max_height):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "height")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0.5, 0.5, 0.5)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Height") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        camera_data = tree.nodes.new('ShaderNodeCameraData')

        map_range = tree.nodes.new('ShaderNodeMapRange')
        map_range.inputs[1].default_value = data.camera_height - max_height
        map_range.inputs[2].default_value = data.camera_height + max_height
        map_range.inputs[3].default_value = 1
        map_range.inputs[4].default_value = 0

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(camera_data.outputs["View Z Depth"], map_range.inputs["Value"])
        tree.links.new(map_range.outputs["Result"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Height"):
            bpy.ops.render.render(write_still=True)


def bake_depth(data, context, settings, max_depth):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "depth")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (1.0, 1.0, 1.0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Depth") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        camera_data = tree.nodes.new('ShaderNodeCameraData')

        map_range = tree.nodes.new('ShaderNodeMapRange')
        map_range.inputs[1].default_value = 0.0
        map_range.inputs[2].default_value = max_depth
        map_range.inputs[3].default_value = 0.0
        map_range.inputs[4].default_value = 1.0

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(camera_data.outputs["View Distance"], map_range.inputs["Value"])
        tree.links.new(map_range.outputs["Result"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Depth"):
            bpy.ops.render.render(write_still=True)


# TODO output RGBA instead of RGB
def bake_color(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "color")
    context.scene.render.image_settings.color_mode = 'RGB'
    render_engine(context, data)
    view_transform_color(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Color", "Base Color")


def bake_metallic(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "metallic")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Metallic", "Metallic")


def bake_roughness(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "roughness")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Roughness", "Roughness")


def bake_emission(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "emission")
    context.scene.render.image_settings.color_mode = 'RGB'
    render_engine(context, data)
    view_transform_color(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Emission", "Emission")


# TODO output RGBA instead of RGB
def bake_vertex_color(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "vertex_color")
    context.scene.render.image_settings.color_mode = 'RGB'
    render_engine(context, data)
    view_transform_color(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Vertex_Color") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        vertex_color = tree.nodes.new('ShaderNodeVertexColor')
        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(vertex_color.outputs["Color"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Vertex_Color"):
            bpy.ops.render.render(write_still=True)


def bake_alpha(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "alpha")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Alpha") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        emission = tree.nodes.new('ShaderNodeEmission')

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Alpha"):
            bpy.ops.render.render(write_still=True)


def bake_material_index(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "material_index")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Material_Index") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        object_info = tree.nodes.new('ShaderNodeObjectInfo')

        math = tree.nodes.new('ShaderNodeMath')
        math.operation = 'DIVIDE'
        math.inputs[1].default_value = data.generate_material_index_max

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(object_info.outputs["Material Index"], math.inputs[0])
        tree.links.new(math.outputs["Value"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Material_Index"):
            bpy.ops.render.render(write_still=True)


def bake_object_index(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "object_index")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Object_Index") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        object_info = tree.nodes.new('ShaderNodeObjectInfo')

        math = tree.nodes.new('ShaderNodeMath')
        math.operation = 'DIVIDE'
        math.inputs[1].default_value = data.generate_object_index_max

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(object_info.outputs["Object Index"], math.inputs[0])
        tree.links.new(math.outputs["Value"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Object_Index"):
            bpy.ops.render.render(write_still=True)


def bake_hair_random(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "hair_random")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Hair_Random") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        hair_info = tree.nodes.new('ShaderNodeHairInfo')
        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(hair_info.outputs["Random"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Hair_Random"):
            bpy.ops.render.render(write_still=True)


def bake_hair_root(data, context, settings):
    default_settings(context)
    antialias_off(context)

    context.scene.render.filepath = filename(data, settings, "hair_root")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Hair_Root") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        hair_info = tree.nodes.new('ShaderNodeHairInfo')
        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(hair_info.outputs["Intercept"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Hair_Root"):
            bpy.ops.render.render(write_still=True)


def bake_object_random(data, context, settings):
    default_settings(context)
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "object_random")
    context.scene.render.image_settings.color_mode = 'BW'
    render_engine(context, data)
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Object_Random") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        object_info = tree.nodes.new('ShaderNodeObjectInfo')

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(object_info.outputs["Random"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Object_Random"):
            bpy.ops.render.render(write_still=True)
