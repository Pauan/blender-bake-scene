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
import bmesh


CAMERA_HEIGHT = 50


def make_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


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


def remove_root_collection(data):
    if data.collection:
        remove_collection_recursive(data.collection)

    data.collection = None
    data.height_bounds = None


def safe_remove_collection(collection):
    if len(collection.children) == 0 and len(collection.objects) == 0:
        bpy.data.collections.remove(collection)
        return True

    else:
        return False


def set_mesh_cube(mesh, dimensions):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=False)
    bmesh.ops.scale(bm, vec=dimensions, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()


def set_mesh_plane(mesh, dimensions):
    bm = bmesh.new()
    # This creates a 1m x 1m plane
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=False)
    bmesh.ops.scale(bm, vec=dimensions, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()


def make_mesh_object(name, collection):
    mesh = bpy.data.meshes.new(name=name)
    cube = bpy.data.objects.new(name, mesh)
    collection.objects.link(cube)
    return cube


def make_bounds_object(name, collection):
    obj = make_mesh_object(name, collection)
    obj.display_type = 'BOUNDS'
    obj.show_in_front = True
    obj.hide_select = True
    obj.hide_render = True

    # This causes it to be transparent when using Cycles in the viewport
    obj.cycles_visibility.camera = False
    obj.cycles_visibility.diffuse = False
    obj.cycles_visibility.glossy = False
    obj.cycles_visibility.transmission = False
    obj.cycles_visibility.scatter = False
    obj.cycles_visibility.shadow = False

    return obj


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


def calculate_max_height(context, data):
    size = get_size(context, data)
    half_width = size[0] / 2
    half_height = size[1] / 2

    max_height = 0

    for obj in renderable_objects(context.view_layer.layer_collection):
        if obj.data and obj.type == 'MESH':
            matrix = obj.matrix_world

            for v in obj.data.vertices:
                # Convert to global space
                co = matrix @ v.co

                # If the vertex is within the size bounds
                if (
                    co.x <= half_width and
                    co.x >= -half_width and
                    co.y <= half_height and
                    co.y >= -half_height
                ):
                    height = abs(co.z)

                    if height > CAMERA_HEIGHT:
                        return None

                    if height > max_height:
                        max_height = height

    return max_height


def antialias_on(context):
    context.scene.display.render_aa = '32'
    context.scene.eevee.taa_render_samples = 128

def antialias_off(context):
    context.scene.display.render_aa = 'OFF'
    context.scene.eevee.taa_render_samples = 1


def view_transform_raw(context):
    context.scene.view_settings.view_transform = 'Raw'

def view_transform_color(context):
    context.scene.view_settings.view_transform = 'Standard'

def display_device_rgb(context):
    context.scene.display_settings.display_device = 'sRGB'
    context.scene.sequencer_colorspace_settings.name = 'sRGB'

def default_settings(context):
    context.view_layer.use = True
    context.view_layer.use_pass_combined = True
    context.scene.use_nodes = False
    context.scene.world.use_nodes = False

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

    display_device_rgb(context)

    context.scene.view_settings.look = 'None'
    context.scene.view_settings.exposure = 0
    context.scene.view_settings.gamma = 1
    context.scene.view_settings.use_curve_mapping = False


def filename(data, settings, suffix):
    return settings.filepath + suffix


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
        for obj in self.context.scene.objects:
            if not obj.hide_render and obj.data and obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.name == "":
                        slot.material = self.temp_material

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


def bake_normal(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "normal")
    context.scene.render.image_settings.color_mode = 'RGB'
    context.scene.render.engine = 'BLENDER_EEVEE'
    view_transform_raw(context)
    context.scene.world.color = (0.5, 0.5, 1)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Normal") as tree:
        inputs = tree.nodes.new('NodeGroupInput')

        normalize = tree.nodes.new('ShaderNodeVectorMath')
        normalize.operation = 'NORMALIZE'

        multiply = tree.nodes.new('ShaderNodeVectorMath')
        multiply.operation = 'MULTIPLY'
        multiply.inputs[1].default_value[0] = 0.5
        multiply.inputs[1].default_value[1] = 0.5
        multiply.inputs[1].default_value[2] = 0.5

        add = tree.nodes.new('ShaderNodeVectorMath')
        add.inputs[1].default_value[0] = 0.5
        add.inputs[1].default_value[1] = 0.5
        add.inputs[1].default_value[2] = 0.5

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(inputs.outputs["Normal"], normalize.inputs["Vector"])
        tree.links.new(normalize.outputs["Vector"], multiply.inputs["Vector"])
        tree.links.new(multiply.outputs["Vector"], add.inputs["Vector"])
        tree.links.new(add.outputs["Vector"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Normal"):
            bpy.ops.render.render(write_still=True)


def bake_ao(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "ao")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
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
        ao.samples = 128

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(inputs.outputs["Normal"], ao.inputs["Normal"])
        tree.links.new(ao.outputs["AO"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_AO"):
            bpy.ops.render.render(write_still=True)


def bake_curvature(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "curvature")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
    view_transform_raw(context)
    context.scene.world.color = (0.5, 0.5, 1)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Curvature") as tree:
        inputs = tree.nodes.new('NodeGroupInput')

        normalize = tree.nodes.new('ShaderNodeVectorMath')
        normalize.operation = 'NORMALIZE'

        add = tree.nodes.new('ShaderNodeVectorMath')
        add.inputs[1].default_value[0] = 0.5
        add.inputs[1].default_value[1] = 0.5
        add.inputs[1].default_value[2] = 0

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(inputs.outputs["Normal"], normalize.inputs["Vector"])
        tree.links.new(normalize.outputs["Vector"], add.inputs[0])
        tree.links.new(add.outputs["Vector"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

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
                tree.links.new(combine.outputs["Value"], normalize.inputs[1])
                tree.links.new(normalize.outputs["Value"], outputs.inputs["Image"])

                bpy.ops.render.render(write_still=True)


def bake_height(data, context, settings, max_height):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "height")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
    view_transform_raw(context)
    context.scene.world.color = (0.5, 0.5, 0.5)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    with NodeGroup("__Bake_Height") as tree:
        inputs = tree.nodes.new('NodeGroupInput')
        camera_data = tree.nodes.new('ShaderNodeCameraData')

        map_range = tree.nodes.new('ShaderNodeMapRange')
        map_range.inputs[1].default_value = CAMERA_HEIGHT - max_height
        map_range.inputs[2].default_value = CAMERA_HEIGHT + max_height
        map_range.inputs[3].default_value = 1
        map_range.inputs[4].default_value = 0

        emission = tree.nodes.new('ShaderNodeEmission')

        tree.links.new(camera_data.outputs["View Z Depth"], map_range.inputs["Value"])
        tree.links.new(map_range.outputs["Result"], emission.inputs["Color"])

        node_group_output(tree, inputs, emission.outputs["Emission"])

        with ReplaceMaterials(context, "__Bake_Height"):
            bpy.ops.render.render(write_still=True)


# TODO output RGBA instead of RGB
def bake_color(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "color")
    context.scene.render.image_settings.color_mode = 'RGB'
    context.scene.render.engine = 'BLENDER_EEVEE'
    view_transform_color(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Color", "Base Color")


def bake_metallic(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "metallic")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Metallic", "Metallic")


def bake_roughness(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "roughness")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
    view_transform_raw(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Roughness", "Roughness")


def bake_emission(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "emission")
    context.scene.render.image_settings.color_mode = 'RGB'
    context.scene.render.engine = 'BLENDER_EEVEE'
    view_transform_color(context)
    context.scene.world.color = (0, 0, 0)
    context.scene.eevee.use_gtao = False
    context.scene.eevee.use_overscan = False

    render_with_input(context, "__Bake_Emission", "Emission")


def bake_alpha(data, context, settings):
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "alpha")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
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
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "material_index")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
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
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "object_index")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
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
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "hair_random")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
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
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "hair_root")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
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
    antialias_on(context)

    context.scene.render.filepath = filename(data, settings, "object_random")
    context.scene.render.image_settings.color_mode = 'BW'
    context.scene.render.engine = 'BLENDER_EEVEE'
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


class CalculateMaxHeight(bpy.types.Operator):
    bl_idname = "bake_scene.calculate_max_height"
    bl_label = "Calculate max height"
    bl_description = "Sets the max height using the same algorithm as the Auto mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data = context.scene.bake_scene

        max_height = calculate_max_height(context, data)

        if max_height is None:
            self.report({'ERROR'}, "Objects are outside of baking range (" + str(CAMERA_HEIGHT) + "m)")
        else:
            data.max_height = max_height

        return {'FINISHED'}


class UpdateBounds(bpy.types.Operator):
    bl_idname = "bake_scene.update_bounds"
    bl_label = "Update bounds"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def make_collection(self, context, data):
        if not data.collection:
            data.collection = make_collection("[Bake Scene]", context.scene.collection)

        data.collection.color_tag = 'COLOR_01' # Red
        data.collection.hide_select = True
        data.collection.hide_render = True

    def update_size(self, context, data):
        if data.show_size and False:
            self.make_collection(context, data)

            if not data.size_bounds:
                data.size_bounds = make_bounds_object("[Bake Scene] Size Bounds", data.collection)

            set_mesh_plane(data.size_bounds.data, (data.size, data.size, 1))

        elif data.size_bounds:
            remove_object(data.size_bounds)
            data.size_bounds = None

    def update_height(self, context, data):
        if data.generate_height and data.height_mode == 'MANUAL' and False:
            self.make_collection(context, data)

            if not data.height_bounds:
                data.height_bounds = make_bounds_object("[Bake Scene] Height Bounds", data.collection)

            set_mesh_cube(data.height_bounds.data, (data.size, data.size, data.max_height * 2))

        elif data.height_bounds:
            remove_object(data.height_bounds)
            data.height_bounds = None

    def execute(self, context):
        return {'FINISHED'}
        data = context.scene.bake_scene

        self.update_size(context, data)
        self.update_height(context, data)

        # This cleans up the collection if it doesn't have any objects inside of it
        if data.collection and safe_remove_collection(data.collection):
            data.collection = None

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


# Creates a camera and automatically removes it
class Camera:
    def __init__(self, context, size):
        self.scene = context.scene
        self.size = size
        self.old_camera = None
        self.camera = None

    def __enter__(self):
        name = "[Bake Scene] Camera"
        data = bpy.data.cameras.new(name)

        data.type = 'ORTHO'
        data.ortho_scale = self.size
        data.clip_end = CAMERA_HEIGHT * 2

        self.camera = bpy.data.objects.new(name, data)
        self.scene.collection.objects.link(self.camera)

        self.camera.location = (0, 0, CAMERA_HEIGHT)
        self.camera.hide_render = True
        self.camera.hide_select = True
        self.camera.hide_viewport = True

        self.old_camera = self.scene.camera
        self.scene.camera = self.camera

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
                    self.report({'ERROR'}, "Objects are outside of baking range (" + str(CAMERA_HEIGHT) + "m)")
                    return {'FINISHED'}

            elif data.height_mode == 'MANUAL':
                max_height = data.max_height

        with Settings(context) as settings, Camera(context, data.size), AddEmptyMaterial(context):
            default_settings(context)

            baking = []

            # Geometry
            if data.generate_alpha:
                baking.append(lambda: bake_alpha(data, context, settings))

            if data.generate_ao:
                baking.append(lambda: bake_ao(data, context, settings))

            if data.generate_curvature:
                baking.append(lambda: bake_curvature(data, context, settings))

            if data.generate_height:
                baking.append(lambda: bake_height(data, context, settings, max_height))

            if data.generate_normal:
                baking.append(lambda: bake_normal(data, context, settings))

            # Material
            if data.generate_color:
                baking.append(lambda: bake_color(data, context, settings))

            if data.generate_emission:
                baking.append(lambda: bake_emission(data, context, settings))

            if data.generate_metallic:
                baking.append(lambda: bake_metallic(data, context, settings))

            if data.generate_roughness:
                baking.append(lambda: bake_roughness(data, context, settings))

            # Masking
            if data.generate_material_index:
                baking.append(lambda: bake_material_index(data, context, settings))

            if data.generate_object_index:
                baking.append(lambda: bake_object_index(data, context, settings))

            if data.generate_object_random:
                baking.append(lambda: bake_object_random(data, context, settings))

            # Hair
            if data.generate_hair_random:
                baking.append(lambda: bake_hair_random(data, context, settings))

            if data.generate_hair_root:
                baking.append(lambda: bake_hair_root(data, context, settings))

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
