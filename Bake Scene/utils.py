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
from mathutils import (Vector)


def renderable_objects(layer):
    if not layer.exclude and not layer.collection.hide_render:
        for obj in layer.collection.objects:
            if not obj.hide_render:
                yield obj

        for child in layer.children:
            yield from renderable_objects(child)


def get_size(context, data):
    res_x = context.scene.render.resolution_x
    res_y = context.scene.render.resolution_y

    if res_x == res_y:
        return (data.size, data.size)
    elif res_x < res_y:
        return (data.size * (res_x / res_y), data.size)
    else:
        return (data.size, data.size * (res_y / res_x))


def object_vertices(obj):
    matrix = obj.matrix_world

    # TODO handle particle hair
    if obj.data and obj.type == 'MESH':
        # TODO it should do a bounding box test first to avoid this expensive iteration
        for v in obj.data.vertices:
            # Convert to global space
            yield matrix @ v.co

    else:
        # TODO instead of using the vertices, it should instead do a box intersection test
        for a in obj.bound_box:
            # Convert to global space
            yield matrix @ Vector(a)


def calculate_max_height(context, data):
    size = get_size(context, data)
    half_width = size[0] / 2
    half_height = size[1] / 2

    camera_height = data.camera_height

    max_height = 0

    for obj in renderable_objects(context.view_layer.layer_collection):
        for co in object_vertices(obj):
            # If the vertex is within the size bounds
            if (
                co.x <= half_width and
                co.x >= -half_width and
                co.y <= half_height and
                co.y >= -half_height
            ):
                height = abs(co.z)

                # Abort if the vertex is outside of the camera frustrum
                if height > camera_height:
                    return None

                if height > max_height:
                    max_height = height

    return max_height


def antialias_on(context):
    context.scene.cycles.samples = 32
    context.scene.display.render_aa = '32'
    context.scene.eevee.taa_render_samples = 128

def antialias_off(context):
    context.scene.cycles.samples = 1
    context.scene.display.render_aa = 'OFF'
    context.scene.eevee.taa_render_samples = 1


def view_transform_raw(context):
    context.scene.view_settings.view_transform = 'Raw'

def view_transform_color(context):
    context.scene.view_settings.view_transform = 'Standard'


def render_engine(context, data):
    if data.camera_mode == 'TOP':
        context.scene.render.engine = 'BLENDER_EEVEE'

    elif data.camera_mode == 'HDRI':
        context.scene.render.engine = 'CYCLES'


def default_settings(context):
    context.view_layer.use = True
    context.view_layer.use_pass_combined = True
    context.scene.use_nodes = False
    context.scene.world.use_nodes = False

    context.scene.cycles.use_adaptive_sampling = False
    context.scene.cycles.time_limit = 0
    context.scene.cycles.use_denoising = False
    context.scene.cycles.scrambling_distance = 0

    context.scene.eevee.use_bloom = False
    context.scene.eevee.use_ssr = False
    context.scene.eevee.use_motion_blur = False

    context.scene.render.film_transparent = False
    context.scene.render.use_single_layer = True
    context.scene.render.use_freestyle = False
    context.scene.render.use_border = False
    context.scene.render.use_multiview = False
    context.scene.render.use_file_extension = True
    context.scene.render.use_overwrite = True
    context.scene.render.use_stamp = False
    context.scene.render.use_high_quality_normals = True
    context.scene.render.use_compositing = False
    context.scene.render.use_sequencer = False
    context.scene.render.dither_intensity = 0

    context.scene.display.shading.light = 'FLAT'
    context.scene.display.shading.show_backface_culling = False
    context.scene.display.shading.show_xray = False
    context.scene.display.shading.show_shadows = False
    context.scene.display.shading.use_dof = False
    context.scene.display.shading.show_object_outline = False
    context.scene.display.matcap_ssao_samples = 500
    context.scene.display.matcap_ssao_distance = 0

    context.scene.display_settings.display_device = 'sRGB'
    context.scene.sequencer_colorspace_settings.name = 'sRGB'

    context.scene.view_settings.look = 'None'
    context.scene.view_settings.exposure = 0
    context.scene.view_settings.gamma = 1
    context.scene.view_settings.use_curve_mapping = False


def filename(data, settings, suffix):
    return settings.filepath + suffix


def node_group_output(tree, inputs, socket):
    mix = tree.nodes.new('ShaderNodeMixShader')
    transparent = tree.nodes.new('ShaderNodeBsdfTransparent')

    outputs = tree.nodes.new('ShaderNodeOutputMaterial')
    outputs.is_active_output = True

    tree.links.new(inputs.outputs["Alpha"], mix.inputs[0])
    tree.links.new(transparent.outputs["BSDF"], mix.inputs[1])
    tree.links.new(socket, mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], outputs.inputs["Surface"])


def render_with_input(context, name, input):
    with NodeGroup(name) as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(inputs.outputs[input], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, name):
            bpy.ops.render.render(write_still=True)


# Creates a node group for custom materials
class NodeGroup:
    def __init__(self, name):
        self.name = name
        self.node_tree = None

    def __enter__(self):
        self.node_tree = bpy.data.node_groups.new(self.name, 'ShaderNodeTree')
        self.node_tree.use_fake_user = False

        self.node_tree.inputs.new('NodeSocketColor', "Base Color")
        self.node_tree.inputs.new('NodeSocketFloat', "Metallic")
        self.node_tree.inputs.new('NodeSocketFloat', "Roughness")
        self.node_tree.inputs.new('NodeSocketColor', "Emission")
        self.node_tree.inputs.new('NodeSocketFloat', "Alpha").default_value = 1.0
        self.node_tree.inputs.new('NodeSocketVector', "Normal")

        return self.node_tree

    def __exit__(self, exc_type, exc_value, traceback):
        bpy.data.node_groups.remove(self.node_tree)
        return False


# Creates a node group for custom compositor
class CompositorNodeGroup:
    def __init__(self, scene, name):
        self.name = name

        self.scene = scene
        self.use_nodes = True
        self.use_compositing = True

        self.node_group = None
        self.input_node = None
        self.node = None

        self.output_nodes = []

    def __enter__(self):
        self.use_nodes = self.scene.use_nodes
        self.use_compositing = self.scene.render.use_compositing

        self.scene.use_nodes = True
        self.scene.render.use_compositing = True

        # Mute existing Composite nodes
        for node in self.scene.node_tree.nodes:
            if node.type == 'COMPOSITE':
                self.output_nodes.append({
                    "node": node,
                    "mute": node.mute,
                })
                node.mute = True

        # Create node group
        self.node_group = bpy.data.node_groups.new(self.name, 'CompositorNodeTree')
        self.node_group.use_fake_user = False

        self.node_group.inputs.new('NodeSocketImage', "Image")

        # Create Render Layers node
        self.input_node = self.scene.node_tree.nodes.new('CompositorNodeRLayers')

        # Create and link node group
        self.node = self.scene.node_tree.nodes.new('CompositorNodeGroup')
        self.node.node_tree = self.node_group
        self.node.name = self.node_group.name

        self.scene.node_tree.links.new(self.input_node.outputs["Image"], self.node.inputs["Image"])

        return self.node.node_tree

    def __exit__(self, exc_type, exc_value, traceback):
        if self.node is not None:
            self.scene.node_tree.nodes.remove(self.node)

        if self.input_node is not None:
            self.scene.node_tree.nodes.remove(self.input_node)

        for info in self.output_nodes:
            info["node"].mute = info["mute"]

        if self.node_group is not None:
            bpy.data.node_groups.remove(self.node_group)

        self.scene.use_nodes = self.use_nodes
        self.scene.render.use_compositing = self.use_compositing

        return False


# Adds a placeholder material to every empty material slot
class AddEmptyMaterial:
    def __init__(self, context):
        self.context = context
        self.temp_material = None

    def __enter__(self):
        self.temp_material = bpy.data.materials.new("__Bake_Temporary")
        self.temp_material.use_nodes = True
        self.temp_material.node_tree.nodes.remove(self.temp_material.node_tree.nodes.get("Principled BSDF"))

        # Adds the temporary material to every empty material slot
        for obj in renderable_objects(self.context.view_layer.layer_collection):
            for slot in obj.material_slots:
                if slot.name == "":
                    slot.material = self.temp_material

            # TODO it should remove the material slot afterwards
            if not obj.active_material or obj.active_material.name == "":
                obj.active_material = self.temp_material

    def __exit__(self, exc_type, exc_value, traceback):
        bpy.data.materials.remove(self.temp_material)
        return False


# Replaces all of the materials with a custom material
class ReplaceMaterials:
    def __init__(self, context, name):
        self.context = context
        self.name = name
        self.saved = {}

    def __enter__(self):
        for mat in bpy.data.materials:
            use_nodes = mat.use_nodes
            mat.use_nodes = True

            # Add in the node group to the material
            node_group = mat.node_tree.nodes.new('ShaderNodeGroup')
            node_tree = bpy.data.node_groups[self.name]
            node_group.node_tree = node_tree
            node_group.name = node_tree.name

            output_nodes = []
            active_node = None

            # Mute existing Output Material nodes
            for node in mat.node_tree.nodes:
                if node.type == 'OUTPUT_MATERIAL':
                    if node.is_active_output:
                        active_node = node

                    output_nodes.append({
                        "node": node,
                        "mute": node.mute,
                    })

                    node.mute = True

            # Get node which is currently linked to the Output Material
            if active_node:
                for link in active_node.inputs["Surface"].links:
                    # Connects the color, metallic, roughness, and emission to the group
                    if link.from_node.type == 'BSDF_PRINCIPLED':
                        for input in link.from_node.inputs:
                            if input.name in ("Base Color", "Metallic", "Roughness", "Emission", "Alpha", "Normal"):
                                socket = node_group.inputs[input.name]

                                if input.is_linked:
                                    for input_link in input.links:
                                        mat.node_tree.links.new(input_link.from_socket, socket)
                                        break
                                else:
                                    socket.default_value = input.default_value

                    break

            normal_socket = node_group.inputs["Normal"]

            geometry_node = None

            # If Normal is unlinked, use the Geometry Normal as the default
            if not normal_socket.is_linked:
                geometry_node = mat.node_tree.nodes.new('ShaderNodeNewGeometry')
                mat.node_tree.links.new(geometry_node.outputs["Normal"], normal_socket)

            self.saved[mat.name] = {
                "use_nodes": use_nodes,
                "output_nodes": output_nodes,
                "geometry_node": geometry_node,
                "node_group": node_group,
            }

    def __exit__(self, exc_type, exc_value, traceback):
        for mat in bpy.data.materials:
            saved = self.saved.get(mat.name, None)

            if saved:
                mat.node_tree.nodes.remove(saved["node_group"])

                geometry_node = saved["geometry_node"]

                if geometry_node:
                    mat.node_tree.nodes.remove(geometry_node)

                for info in saved["output_nodes"]:
                    info["node"].mute = info["mute"]

                mat.use_nodes = saved["use_nodes"]

        return False


# Creates a camera and automatically removes it
class Camera:
    def __init__(self, context):
        self.scene = context.scene
        self.old_camera = None
        self.camera = None

    def __enter__(self):
        name = "[Bake Scene] Camera"
        data = bpy.data.cameras.new(name)

        self.camera = bpy.data.objects.new(name, data)
        self.scene.collection.objects.link(self.camera)

        self.camera.hide_render = True
        self.camera.hide_select = True
        self.camera.hide_viewport = True

        self.old_camera = self.scene.camera
        self.scene.camera = self.camera
        return self.camera

    def __exit__(self, exc_type, exc_value, traceback):
        data = self.camera.data
        bpy.data.objects.remove(self.camera)
        bpy.data.cameras.remove(data)

        self.scene.camera = self.old_camera

        return False


# Saves the user's settings and automatically restores them
class Settings:
    def __init__(self, context):
        scene = context.scene
        view_layer = context.view_layer

        self.scene = scene
        self.view_layer = view_layer

        self.use_compositor = scene.use_nodes
        self.use_background = scene.world.use_nodes
        self.background_color = scene.world.color.copy()

        self.engine = scene.render.engine
        self.film_transparent = scene.render.film_transparent
        self.use_single_layer = scene.render.use_single_layer
        self.use_freestyle = scene.render.use_freestyle
        self.use_border = scene.render.use_border
        self.use_multiview = scene.render.use_multiview
        self.filepath = scene.render.filepath
        self.use_file_extension = scene.render.use_file_extension
        self.use_overwrite = scene.render.use_overwrite
        self.use_stamp = scene.render.use_stamp
        self.use_high_quality_normals = scene.render.use_high_quality_normals
        self.use_compositing = scene.render.use_compositing
        self.use_sequencer = scene.render.use_sequencer
        self.dither_intensity = scene.render.dither_intensity

        self.color_mode = scene.render.image_settings.color_mode

        self.render_aa = scene.display.render_aa
        self.light = scene.display.shading.light
        self.color_type = scene.display.shading.color_type
        self.single_color = scene.display.shading.single_color.copy()
        self.show_backface_culling = scene.display.shading.show_backface_culling
        self.show_xray = scene.display.shading.show_xray
        self.show_shadows = scene.display.shading.show_shadows
        self.show_cavity = scene.display.shading.show_cavity
        self.cavity_type = scene.display.shading.cavity_type
        self.curvature_ridge_factor = scene.display.shading.curvature_ridge_factor
        self.curvature_valley_factor = scene.display.shading.curvature_valley_factor
        self.use_dof = scene.display.shading.use_dof
        self.show_object_outline = scene.display.shading.show_object_outline
        self.matcap_ssao_distance = scene.display.matcap_ssao_distance
        self.matcap_ssao_samples = scene.display.matcap_ssao_samples

        self.display_device = scene.display_settings.display_device

        self.view_transform = scene.view_settings.view_transform
        self.look = scene.view_settings.look
        self.exposure = scene.view_settings.exposure
        self.gamma = scene.view_settings.gamma
        self.use_curve_mapping = scene.view_settings.use_curve_mapping

        self.sequencer = scene.sequencer_colorspace_settings.name

        self.cycle_sample = scene.cycles.samples
        self.use_adaptive_sampling = scene.cycles.use_adaptive_sampling
        self.time_limit = scene.cycles.time_limit
        self.use_denoising = scene.cycles.use_denoising
        self.scrambling_distance = scene.cycles.scrambling_distance

        self.taa_render_samples = scene.eevee.taa_render_samples
        self.use_gtao = scene.eevee.use_gtao
        self.use_bloom = scene.eevee.use_bloom
        self.use_ssr = scene.eevee.use_ssr
        self.use_motion_blur = scene.eevee.use_motion_blur
        self.use_overscan = scene.eevee.use_overscan
        self.overscan_size = scene.eevee.overscan_size
        self.gtao_distance = scene.eevee.gtao_distance
        self.gtao_factor = scene.eevee.gtao_factor
        self.gtao_quality = scene.eevee.gtao_quality
        self.use_gtao_bent_normals = scene.eevee.use_gtao_bent_normals
        self.use_gtao_bounce = scene.eevee.use_gtao_bounce

        self.use = view_layer.use
        self.use_pass_combined = view_layer.use_pass_combined

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        scene = self.scene
        view_layer = self.view_layer

        scene.use_nodes = self.use_compositor
        scene.world.use_nodes = self.use_background
        scene.world.color = self.background_color

        scene.render.engine = self.engine
        scene.render.film_transparent = self.film_transparent
        scene.render.use_single_layer = self.use_single_layer
        scene.render.use_freestyle = self.use_freestyle
        scene.render.use_border = self.use_border
        scene.render.use_multiview = self.use_multiview
        scene.render.filepath = self.filepath
        scene.render.use_file_extension = self.use_file_extension
        scene.render.use_overwrite = self.use_overwrite
        scene.render.use_stamp = self.use_stamp
        scene.render.use_high_quality_normals = self.use_high_quality_normals
        scene.render.use_compositing = self.use_compositing
        scene.render.use_sequencer = self.use_sequencer
        scene.render.dither_intensity = self.dither_intensity

        scene.render.image_settings.color_mode = self.color_mode

        scene.display.render_aa = self.render_aa
        scene.display.shading.light = self.light
        scene.display.shading.color_type = self.color_type
        scene.display.shading.single_color = self.single_color
        scene.display.shading.show_backface_culling = self.show_backface_culling
        scene.display.shading.show_xray = self.show_xray
        scene.display.shading.show_shadows = self.show_shadows
        scene.display.shading.show_cavity = self.show_cavity
        scene.display.shading.cavity_type = self.cavity_type
        scene.display.shading.curvature_ridge_factor = self.curvature_ridge_factor
        scene.display.shading.curvature_valley_factor = self.curvature_valley_factor
        scene.display.shading.use_dof = self.use_dof
        scene.display.shading.show_object_outline = self.show_object_outline
        scene.display.matcap_ssao_distance = self.matcap_ssao_distance
        scene.display.matcap_ssao_samples = self.matcap_ssao_samples

        scene.display_settings.display_device = self.display_device

        scene.view_settings.view_transform = self.view_transform
        scene.view_settings.look = self.look
        scene.view_settings.exposure = self.exposure
        scene.view_settings.gamma = self.gamma
        scene.view_settings.use_curve_mapping = self.use_curve_mapping

        scene.sequencer_colorspace_settings.name = self.sequencer

        scene.cycles.samples = self.cycle_sample
        scene.cycles.use_adaptive_sampling = self.use_adaptive_sampling
        scene.cycles.time_limit = self.time_limit
        scene.cycles.use_denoising = self.use_denoising
        scene.cycles.scrambling_distance = self.scrambling_distance

        scene.eevee.taa_render_samples = self.taa_render_samples
        scene.eevee.use_gtao = self.use_gtao
        scene.eevee.use_bloom = self.use_bloom
        scene.eevee.use_ssr = self.use_ssr
        scene.eevee.use_motion_blur = self.use_motion_blur
        scene.eevee.use_overscan = self.use_overscan
        scene.eevee.overscan_size = self.overscan_size
        scene.eevee.gtao_distance = self.gtao_distance
        scene.eevee.gtao_factor = self.gtao_factor
        scene.eevee.gtao_quality = self.gtao_quality
        scene.eevee.use_gtao_bent_normals = self.use_gtao_bent_normals
        scene.eevee.use_gtao_bounce = self.use_gtao_bounce

        view_layer.use = self.use
        view_layer.use_pass_combined = self.use_pass_combined
        return False
