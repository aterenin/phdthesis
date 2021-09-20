import bpy
import bmesh
from functools import partial
import numpy as np
import os
from mathutils import Vector


def reset_scene():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material, do_unlink=True)
    for light in bpy.data.lights:
        bpy.data.lights.remove(light, do_unlink=True)
    for camera in bpy.data.cameras:
        bpy.data.cameras.remove(camera, do_unlink=True)
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection, do_unlink=True)
    for node_group in bpy.data.node_groups:
        bpy.data.node_groups.remove(node_group, do_unlink=True)
    if bpy.context.scene.use_nodes:
        bpy.context.scene.use_nodes = False
        for node in bpy.context.scene.node_tree.nodes:
            bpy.context.scene.node_tree.nodes.remove(node)
    for view_layer in bpy.context.scene.view_layers:
        if view_layer.name != "View Layer":
            bpy.context.scene.view_layers.remove(view_layer)
        else:
            view_layer.use = True


def cleanup(objects = None, materials = None, modifiers = None, force = False):
    if bpy.app.background or force:
        if materials is not None:
            for material in materials:
                bpy.data.materials.remove(material, do_unlink=True)
        if modifiers is not None:
            for modifier in modifiers:
                if modifier.type == "NODES":
                    bpy.data.node_groups.remove(modifier.node_group, do_unlink=True)
        if objects is not None:
            for obj in objects:
                bpy.data.objects.remove(obj, do_unlink=True)


def set_renderer_settings(num_samples = 128):
    bpy.data.scenes["Scene"].render.engine = "CYCLES"
    bpy.data.scenes["Scene"].cycles.device = "GPU"
    bpy.data.scenes["Scene"].cycles.samples = num_samples
    bpy.data.scenes["Scene"].cycles.use_denoising = True
    bpy.data.scenes["Scene"].cycles.denoiser = "OPENIMAGEDENOISE"
    bpy.data.scenes["Scene"].cycles.use_preview_denoising = True
    bpy.data.scenes["Scene"].view_settings.look = "High Contrast"
    


@partial(np.vectorize, signature = "()->()")
def srgb_to_linear(color):
    if color < 0.04045:
        return color / 12.92 
    else:
        return ((color + 0.055) / 1.055)**2.4


@partial(np.vectorize, signature = "()->()")
def linear_to_srgb(color):
    if color < 0.0031308:
        return 12.92 * color 
    else:
        return color**(1 / 2.4) * 1.055 - 0.055
        

def import_bmesh(mesh_file):
    bpy.ops.import_scene.obj(filepath=mesh_file, split_mode = "OFF")
    obj = bpy.context.selected_objects[0]
    mesh = obj.data
    mat = obj.data.materials[0]
    
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    bpy.data.objects.remove(obj, do_unlink = True)
    bpy.data.meshes.remove(mesh, do_unlink = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    
    return bm


def import_color(bm, data_file = None, palette_file = None, color = None, bounds = None):
    if color is None:
        data = np.genfromtxt(data_file, delimiter=",")
        if bounds is None:
            min = data.min()
            max = data.max()
        else:
            (min,max) = bounds
        data_std = (data - min) / (max - min)
        color_palette = np.genfromtxt(palette_file, delimiter=",")
        if color_palette.shape[0] == 3:
            color_palette = np.vstack((color_palette, np.ones((1,color_palette.shape[1]))))
        colors = np.vstack((
            np.interp(data_std, np.linspace(0,1,256), color_palette[0,:]),
            np.interp(data_std, np.linspace(0,1,256), color_palette[1,:]),
            np.interp(data_std, np.linspace(0,1,256), color_palette[2,:]),
            np.interp(data_std, np.linspace(0,1,256), color_palette[3,:]),
        ))
    else:
        colors = np.repeat(np.array(color)[:,np.newaxis], len(bm.verts), axis=-1)
    
    if bm.loops.layers.color.active is not None:
        bm.loops.layers.color.remove(bm.loops.layers.color.active)
    
    color_layer = bm.loops.layers.color.new("color")
    for face in bm.faces:
        for loop in face.loops:
            loop[color_layer] = colors[:,loop.vert.index]
    

def add_mesh(bm, name="Mesh"):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm.to_mesh(mesh)

    return obj
    

def add_vertex_colors(obj, shade_smooth = True):
    mat = bpy.data.materials.new(name = "Surface Color")
    mat.use_nodes = True
    
    vertex_color_node = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    shader_node = mat.node_tree.nodes["Principled BSDF"]
    
    mat.node_tree.links.new(vertex_color_node.outputs["Color"], shader_node.inputs["Base Color"])
    mat.node_tree.links.new(vertex_color_node.outputs["Alpha"], shader_node.inputs["Alpha"])
    
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    if shade_smooth:
        obj.data.polygons.foreach_set("use_smooth",  [True] * len(obj.data.polygons))
        obj.data.update()
    
    return mat
    
    
def import_vector_field(vf_file):
    vector_field = np.genfromtxt(vf_file, delimiter=",")

    bm = bmesh.new()
    arrow_layer = bm.verts.layers.float_vector.new("arrow")
    normal_x_layer = bm.verts.layers.float_vector.new("normal_x")
    normal_z_layer = bm.verts.layers.float_vector.new("normal_z")
    for row in vector_field:
        vert = bm.verts.new(row[0:3])
        vert[arrow_layer] = row[3:6]
        if row.size == 12:
            vert[normal_x_layer] = row[6:9]
            vert[normal_z_layer] = row[9:12]
        else:
            if np.all(row[3:6] == 0):
                vert[normal_x_layer] = np.zeros(3)
                vert[normal_z_layer] = np.zeros(3)
            else:
                length = np.linalg.norm(row[3:6])
                arrow = row[3:6] / length
                axis = np.array((0,0,1)) if np.allclose(arrow,np.array((1,0,0))) or np.allclose(arrow,np.array((-1,0,0))) else np.array((1,0,0))
                normal_x = np.cross(arrow, axis)
                unit_x = normal_x / np.linalg.norm(normal_x)
                normal_z = np.cross(arrow, normal_x)
                unit_z = normal_z / np.linalg.norm(normal_z)
                vert[normal_x_layer] = length * unit_x
                vert[normal_z_layer] = length * unit_z

    return bm


def add_vector_field(vec_bm, arr_obj, scale = 1):
    vf_mesh = bpy.data.meshes.new("Vector Field")
    vf_obj = bpy.data.objects.new("Vector Field", vf_mesh)
    vec_bm.to_mesh(vf_mesh)
    bpy.context.scene.collection.objects.link(vf_obj)

    mod = vf_obj.modifiers.new("Vector Field", "NODES")
    input_node = mod.node_group.nodes["Group Input"]
    output_node = mod.node_group.nodes["Group Output"]
    arrow_length_node = mod.node_group.nodes.new("GeometryNodeAttributeVectorMath")
    arrow_length_node.operation = "LENGTH"
    arrow_length_node.inputs["A"].default_value = "arrow"
    arrow_length_node.inputs["Result"].default_value = "arrow_length"
    normal_x_length_node = mod.node_group.nodes.new("GeometryNodeAttributeVectorMath")
    normal_x_length_node.operation = "LENGTH"
    normal_x_length_node.inputs["A"].default_value = "normal_x"
    normal_x_length_node.inputs["Result"].default_value = "normal_x_length"
    normal_z_length_node = mod.node_group.nodes.new("GeometryNodeAttributeVectorMath")
    normal_z_length_node.operation = "LENGTH"
    normal_z_length_node.inputs["A"].default_value = "normal_z"
    normal_z_length_node.inputs["Result"].default_value = "normal_z_length"
    combine_node = mod.node_group.nodes.new("GeometryNodeAttributeCombineXYZ")
    combine_node.input_type_x = "ATTRIBUTE"
    combine_node.inputs["X"].default_value = "normal_x_length"
    combine_node.input_type_y = "ATTRIBUTE"
    combine_node.inputs["Y"].default_value = "arrow_length"
    combine_node.input_type_z = "ATTRIBUTE"
    combine_node.inputs["Z"].default_value = "normal_z_length"
    combine_node.inputs["Result"].default_value = "arrow_scale"
    arrow_scale_node = mod.node_group.nodes.new("GeometryNodePointScale")
    arrow_scale_node.input_type = "ATTRIBUTE"
    arrow_scale_node.inputs["Factor"].default_value = "arrow_scale"
    constant_scale_node  = mod.node_group.nodes.new("GeometryNodePointScale")
    constant_scale_node.input_type = "FLOAT"
    constant_scale_node.inputs[3].default_value = scale
    align_rotation_normal_node = mod.node_group.nodes.new("GeometryNodeAlignRotationToVector")
    align_rotation_normal_node.axis = "X"
    align_rotation_normal_node.input_type_vector = "ATTRIBUTE"
    align_rotation_normal_node.inputs["Vector"].default_value = "normal_x"
    align_rotation_node = mod.node_group.nodes.new("GeometryNodeAlignRotationToVector")
    align_rotation_node.axis = "Y"
    align_rotation_node.input_type_vector = "ATTRIBUTE"
    align_rotation_node.inputs["Vector"].default_value = "arrow"
    point_instance_node = mod.node_group.nodes.new("GeometryNodePointInstance")
    point_instance_node.inputs["Object"].default_value = arr_obj

    mod.node_group.links.clear()
    mod.node_group.links.new(input_node.outputs["Geometry"], arrow_length_node.inputs["Geometry"])
    mod.node_group.links.new(arrow_length_node.outputs["Geometry"], normal_x_length_node.inputs["Geometry"])
    mod.node_group.links.new(normal_x_length_node.outputs["Geometry"], normal_z_length_node.inputs["Geometry"])
    mod.node_group.links.new(normal_z_length_node.outputs["Geometry"], combine_node.inputs["Geometry"])
    mod.node_group.links.new(combine_node.outputs["Geometry"], arrow_scale_node.inputs["Geometry"])
    mod.node_group.links.new(arrow_scale_node.outputs["Geometry"], constant_scale_node.inputs["Geometry"])
    mod.node_group.links.new(constant_scale_node.outputs["Geometry"], align_rotation_normal_node.inputs["Geometry"])
    mod.node_group.links.new(align_rotation_normal_node.outputs["Geometry"], align_rotation_node.inputs["Geometry"])
    mod.node_group.links.new(align_rotation_node.outputs["Geometry"], point_instance_node.inputs["Geometry"])
    mod.node_group.links.new(point_instance_node.outputs["Geometry"], output_node.inputs["Geometry"])

    return vf_obj


def create_vector_arrow(length = 10, ratio = 0.1, vertices = 25):
    bm = bmesh.new()
    prod = np.pi**2 * ratio**2 / length**2
    shift = (prod - 2 * np.sqrt(-prod * ratio**2 + prod + 4*ratio**2)) / (prod - 4)
    scale = 1 - shift

    for theta in np.linspace(np.pi/2, np.pi, vertices//2):
        bm.verts.new((0, length - ratio * np.cos(theta), ratio * np.sin(theta)))

    for theta in np.linspace(0, np.pi/2, vertices//2):
        bm.verts.new((0, -np.cos(theta), np.sin(theta)))

    for x in np.linspace(0,length,vertices)[1:-1]:
        bm.verts.new((0, length - x, scale * np.sin(x / length * np.pi / 2) + shift))

    bmesh.ops.spin(bm, geom = bm.verts[:] + bm.edges[:], angle = 2*np.pi, steps = vertices, axis = (0,1,0), cent = (0,0,0))

    mesh = bpy.data.meshes.new("Arrow")
    obj = bpy.data.objects.new("Arrow", mesh)
    bm.to_mesh(mesh)
    bpy.context.scene.collection.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.convex_hull()
    bpy.ops.object.editmode_toggle()
    
    obj.data.polygons.foreach_set("use_smooth",  [True] * len(obj.data.polygons))
    obj.data.update()

    mat = bpy.data.materials.new(name = "Black Surface")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0,0,0,1)
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    obj.hide_set(True)
    obj.hide_render = True

    bm.free()

    return obj


def create_dot(location = (0,0,0), radius = 1, color = (0,0,0,1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions = 5, diameter = radius*2)

    color_layer = bm.loops.layers.color.new("color")
    for face in bm.faces:
        for loop in face.loops:
            loop[color_layer] = color
            
    mesh = bpy.data.meshes.new("Dot")
    obj = bpy.data.objects.new("Dot", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm.to_mesh(mesh)
    bm.free()
            
    obj.data.polygons.foreach_set("use_smooth",  [True] * len(obj.data.polygons))
    obj.data.update()
    obj.location = location
    
    return obj
    

def create_linear_to_srgb_bw_node_group():
    group = bpy.data.node_groups.new(type = "CompositorNodeTree", name = "Linear to sRGB BW")
    group.inputs.new("NodeSocketFloat", "Value")
    group.outputs.new("NodeSocketFloat", "Value")
    
    input = group.nodes.new("NodeGroupInput")
    
    lower_less_than = group.nodes.new("CompositorNodeMath")
    lower_less_than.operation = "LESS_THAN"
    lower_less_than.inputs[1].default_value = 0.0031308
    lower_first_multiply = group.nodes.new("CompositorNodeMath")
    lower_first_multiply.operation = "MULTIPLY"
    lower_second_multiply = group.nodes.new("CompositorNodeMath")
    lower_second_multiply.operation = "MULTIPLY"
    lower_second_multiply.inputs[1].default_value = 12.92
    
    upper_greater_than = group.nodes.new("CompositorNodeMath")
    upper_greater_than.operation = "GREATER_THAN"
    upper_greater_than.inputs[1].default_value = 0.0031308
    upper_first_multiply = group.nodes.new("CompositorNodeMath")
    upper_first_multiply.operation = "MULTIPLY"
    upper_power = group.nodes.new("CompositorNodeMath")
    upper_power.operation = "POWER"
    upper_power.inputs[1].default_value = 1/2.4
    upper_second_multiply = group.nodes.new("CompositorNodeMath")
    upper_second_multiply.operation = "MULTIPLY"
    upper_second_multiply.inputs[1].default_value = 1.055
    upper_subtract = group.nodes.new("CompositorNodeMath")
    upper_subtract.operation = "SUBTRACT"
    upper_subtract.inputs[1].default_value = 0.055
    upper_third_multiply = group.nodes.new("CompositorNodeMath")
    upper_third_multiply.operation = "MULTIPLY"
    
    combined_add = group.nodes.new("CompositorNodeMath")
    
    output = group.nodes.new("NodeGroupOutput")
    
    group.links.new(input.outputs["Value"], lower_less_than.inputs[0])
    group.links.new(input.outputs["Value"], lower_first_multiply.inputs[1])
    group.links.new(input.outputs["Value"], upper_greater_than.inputs[0])
    group.links.new(input.outputs["Value"], upper_first_multiply.inputs[1])
    
    group.links.new(lower_less_than.outputs["Value"], lower_first_multiply.inputs[0])
    group.links.new(lower_first_multiply.outputs["Value"], lower_second_multiply.inputs[0])
    group.links.new(lower_second_multiply.outputs["Value"], combined_add.inputs[0])
    
    group.links.new(upper_greater_than.outputs["Value"], upper_first_multiply.inputs[0])
    group.links.new(upper_greater_than.outputs["Value"], upper_third_multiply.inputs[1])
    group.links.new(upper_first_multiply.outputs["Value"], upper_power.inputs[0])
    group.links.new(upper_power.outputs["Value"], upper_second_multiply.inputs[0])
    group.links.new(upper_second_multiply.outputs["Value"], upper_subtract.inputs[0])
    group.links.new(upper_subtract.outputs["Value"], upper_third_multiply.inputs[0])
    group.links.new(upper_third_multiply.outputs["Value"], combined_add.inputs[1])
    
    group.links.new(combined_add.outputs["Value"], output.inputs["Value"])


def create_srgb_to_linear_bw_node_group():
    group = bpy.data.node_groups.new(type = "CompositorNodeTree", name = "sRGB to Linear BW")
    group.inputs.new("NodeSocketFloat", "Value")
    group.outputs.new("NodeSocketFloat", "Value")
    
    input = group.nodes.new("NodeGroupInput")
    
    lower_less_than = group.nodes.new("CompositorNodeMath")
    lower_less_than.operation = "LESS_THAN"
    lower_less_than.inputs[1].default_value = 0.04045
    lower_multiply = group.nodes.new("CompositorNodeMath")
    lower_multiply.operation = "MULTIPLY"
    lower_divide = group.nodes.new("CompositorNodeMath")
    lower_divide.operation = "DIVIDE"
    lower_divide.inputs[1].default_value = 12.92
    
    upper_greater_than = group.nodes.new("CompositorNodeMath")
    upper_greater_than.operation = "GREATER_THAN"
    upper_greater_than.inputs[1].default_value = 0.04045
    upper_inner_multiply = group.nodes.new("CompositorNodeMath")
    upper_inner_multiply.operation = "MULTIPLY"
    upper_add = group.nodes.new("CompositorNodeMath")
    upper_add.operation = "ADD"
    upper_add.inputs[1].default_value = 0.055
    upper_divide = group.nodes.new("CompositorNodeMath")
    upper_divide.operation = "DIVIDE"
    upper_divide.inputs[1].default_value = 1.055
    upper_power = group.nodes.new("CompositorNodeMath")
    upper_power.operation = "POWER"
    upper_power.inputs[1].default_value = 2.4
    upper_outer_multiply = group.nodes.new("CompositorNodeMath")
    upper_outer_multiply.operation = "MULTIPLY"
    
    combined_add = group.nodes.new("CompositorNodeMath")
    
    output = group.nodes.new("NodeGroupOutput")
    
    group.links.new(input.outputs["Value"], lower_less_than.inputs[0])
    group.links.new(input.outputs["Value"], lower_multiply.inputs[1])
    group.links.new(input.outputs["Value"], upper_greater_than.inputs[0])
    group.links.new(input.outputs["Value"], upper_inner_multiply.inputs[1])
    
    group.links.new(lower_less_than.outputs["Value"], lower_multiply.inputs[0])
    group.links.new(lower_multiply.outputs["Value"], lower_divide.inputs[0])
    group.links.new(lower_divide.outputs["Value"], combined_add.inputs[0])
    
    group.links.new(upper_greater_than.outputs["Value"], upper_inner_multiply.inputs[0])
    group.links.new(upper_greater_than.outputs["Value"], upper_outer_multiply.inputs[1])
    group.links.new(upper_inner_multiply.outputs["Value"], upper_add.inputs[0])
    group.links.new(upper_add.outputs["Value"], upper_divide.inputs[0])
    group.links.new(upper_divide.outputs["Value"], upper_power.inputs[0])
    group.links.new(upper_power.outputs["Value"], upper_outer_multiply.inputs[0])
    group.links.new(upper_outer_multiply.outputs["Value"], combined_add.inputs[1])
    
    group.links.new(combined_add.outputs["Value"], output.inputs["Value"])
    
    
def create_linear_to_srgb_color_node_group():
    group = bpy.data.node_groups.new(type = "CompositorNodeTree", name = "Linear to sRGB Color")
    group.inputs.new("NodeSocketColor", "Image")
    group.outputs.new("NodeSocketColor", "Image")
    
    input = group.nodes.new("NodeGroupInput")
    separate = group.nodes.new("CompositorNodeSepRGBA")
    
    if not "Linear to sRGB BW" in bpy.data.node_groups.keys():
        create_linear_to_srgb_bw_node_group()
    
    red = group.nodes.new("CompositorNodeGroup")
    red.node_tree = bpy.data.node_groups["Linear to sRGB BW"]
    green = group.nodes.new("CompositorNodeGroup")
    green.node_tree = bpy.data.node_groups["Linear to sRGB BW"]
    blue = group.nodes.new("CompositorNodeGroup")
    blue.node_tree = bpy.data.node_groups["Linear to sRGB BW"]
    
    combine = group.nodes.new("CompositorNodeCombRGBA")
    output = group.nodes.new("NodeGroupOutput")
    
    group.links.new(input.outputs["Image"], separate.inputs["Image"])
    group.links.new(separate.outputs["R"], red.inputs["Value"])
    group.links.new(separate.outputs["G"], green.inputs["Value"])
    group.links.new(separate.outputs["B"], blue.inputs["Value"])
    group.links.new(separate.outputs["A"], combine.inputs["A"])
    group.links.new(red.outputs["Value"], combine.inputs["R"])
    group.links.new(green.outputs["Value"], combine.inputs["G"])
    group.links.new(blue.outputs["Value"], combine.inputs["B"])
    group.links.new(combine.outputs["Image"], output.inputs["Image"])


def create_srgb_to_linear_color_node_group():
    group = bpy.data.node_groups.new(type = "CompositorNodeTree", name = "sRGB to Linear Color")
    group.inputs.new("NodeSocketColor", "Image")
    group.outputs.new("NodeSocketColor", "Image")
    
    input = group.nodes.new("NodeGroupInput")
    separate = group.nodes.new("CompositorNodeSepRGBA")
    
    if not "sRGB to Linear BW" in bpy.data.node_groups.keys():
        create_srgb_to_linear_bw_node_group()
    
    red = group.nodes.new("CompositorNodeGroup")
    red.node_tree = bpy.data.node_groups["sRGB to Linear BW"]
    green = group.nodes.new("CompositorNodeGroup")
    green.node_tree = bpy.data.node_groups["sRGB to Linear BW"]
    blue = group.nodes.new("CompositorNodeGroup")
    blue.node_tree = bpy.data.node_groups["sRGB to Linear BW"]
    
    combine = group.nodes.new("CompositorNodeCombRGBA")
    output = group.nodes.new("NodeGroupOutput")
    
    group.links.new(input.outputs["Image"], separate.inputs["Image"])
    group.links.new(separate.outputs["R"], red.inputs["Value"])
    group.links.new(separate.outputs["G"], green.inputs["Value"])
    group.links.new(separate.outputs["B"], blue.inputs["Value"])
    group.links.new(separate.outputs["A"], combine.inputs["A"])
    group.links.new(red.outputs["Value"], combine.inputs["R"])
    group.links.new(green.outputs["Value"], combine.inputs["G"])
    group.links.new(blue.outputs["Value"], combine.inputs["B"])
    group.links.new(combine.outputs["Image"], output.inputs["Image"])


def setup_layers():
    scene = bpy.context.scene
    view_layer = scene.view_layers["View Layer"]
    view_layer.use = False
    object_layer = scene.view_layers.new("Object Layer")
    shadow_layer = scene.view_layers.new("Shadow Layer")
    background_layer = scene.view_layers.new("Background Layer")
    
    object = bpy.data.collections.new("Object")
    scene.collection.children.link(object)
    backdrop = bpy.data.collections.new("Backdrop")
    scene.collection.children.link(backdrop)
    instancing = bpy.data.collections.new("Instancing")
    scene.collection.children.link(instancing)
    
    view_layer.layer_collection.children["Instancing"].exclude = True
    
    object_layer.layer_collection.children["Backdrop"].indirect_only = True
    object_layer.layer_collection.children["Instancing"].exclude = True
    
    shadow_layer.layer_collection.children["Object"].indirect_only = True
    shadow_layer.layer_collection.children["Instancing"].exclude = True
    
    background_layer.layer_collection.children["Object"].exclude = True
    background_layer.layer_collection.children["Instancing"].exclude = True
    

def set_object_collections(object = [], backdrop = [], instancing = []):
    for obj in object:
        bpy.data.collections["Object"].objects.link(obj)
        bpy.context.scene.collection.objects.unlink(obj)
    for obj in backdrop:
        bpy.data.collections["Backdrop"].objects.link(obj)
        bpy.context.scene.collection.objects.unlink(obj)
    for obj in instancing:
        bpy.data.collections["Instancing"].objects.link(obj)
        bpy.context.scene.collection.objects.unlink(obj)


def setup_compositor(mask_center = (0.5,0.15), mask_size = (0.95,0.2), mask_blur_size = 32, shadow_color_correction_exponent = 1):
    scene = bpy.context.scene
    scene.use_nodes = True
    
    object_layer = scene.node_tree.nodes.new("CompositorNodeRLayers")
    object_layer.layer = "Object Layer"
    shadow_layer = scene.node_tree.nodes.new("CompositorNodeRLayers")
    shadow_layer.layer = "Shadow Layer"
    background_layer = scene.node_tree.nodes.new("CompositorNodeRLayers")
    background_layer.layer = "Background Layer"
    
    ratio_node = scene.node_tree.nodes.new("CompositorNodeMixRGB")
    ratio_node.blend_type = "DIVIDE"
    invert_node = scene.node_tree.nodes.new("CompositorNodeInvert")
    rgb_to_bw_node = scene.node_tree.nodes.new("CompositorNodeRGBToBW")
    shadow_color_correction_node = scene.node_tree.nodes.new("CompositorNodeMath")
    shadow_color_correction_node.operation = "POWER"
    shadow_color_correction_node.inputs[1].default_value = shadow_color_correction_exponent
    mask_multiply_node = scene.node_tree.nodes.new("CompositorNodeMath")
    mask_multiply_node.operation = "MULTIPLY"
    
    if not "Linear to sRGB Color" in bpy.data.node_groups.keys():
        create_linear_to_srgb_color_node_group()
    
    linear_to_srgb_node = scene.node_tree.nodes.new("CompositorNodeGroup")
    linear_to_srgb_node.node_tree = bpy.data.node_groups["Linear to sRGB Color"]
    
    subtract_node = scene.node_tree.nodes.new("CompositorNodeMixRGB")
    subtract_node.blend_type = "SUBTRACT"
    add_node = scene.node_tree.nodes.new("CompositorNodeMixRGB")
    add_node.blend_type = "ADD"
    divide_node = scene.node_tree.nodes.new("CompositorNodeMixRGB")
    divide_node.blend_type = "DIVIDE"
    
    set_alpha_node = scene.node_tree.nodes.new("CompositorNodeSetAlpha")
    set_alpha_node.mode = "REPLACE_ALPHA"
    alpha_convert_node = scene.node_tree.nodes.new("CompositorNodePremulKey")
    
    if not "sRGB to Linear Color" in bpy.data.node_groups.keys():
        create_srgb_to_linear_color_node_group()
    
    srgb_to_linear_node = scene.node_tree.nodes.new("CompositorNodeGroup")
    srgb_to_linear_node.node_tree = bpy.data.node_groups["sRGB to Linear Color"]
    
    alpha_over_node = scene.node_tree.nodes.new("CompositorNodeAlphaOver")
    composite_node = scene.node_tree.nodes.new("CompositorNodeComposite")
    viewer_node = scene.node_tree.nodes.new("CompositorNodeViewer")
    
    ellipse_mask_node = scene.node_tree.nodes.new("CompositorNodeEllipseMask")
    ellipse_mask_node.width = mask_size[0]
    ellipse_mask_node.height = mask_size[1]
    ellipse_mask_node.x = mask_center[0]
    ellipse_mask_node.y = mask_center[1]
    
    blur_node = scene.node_tree.nodes.new("CompositorNodeBlur")
    blur_node.size_x = mask_blur_size
    blur_node.size_y = mask_blur_size
    
    scene.node_tree.links.new(shadow_layer.outputs["Image"], ratio_node.inputs[1])
    scene.node_tree.links.new(background_layer.outputs["Image"], ratio_node.inputs[2])
    scene.node_tree.links.new(object_layer.outputs["Image"], alpha_over_node.inputs[2])
    scene.node_tree.links.new(ratio_node.outputs["Image"], linear_to_srgb_node.inputs["Image"])
    scene.node_tree.links.new(ratio_node.outputs["Image"], invert_node.inputs["Color"])
    
    scene.node_tree.links.new(invert_node.outputs["Color"], rgb_to_bw_node.inputs["Image"])
    scene.node_tree.links.new(rgb_to_bw_node.outputs["Val"], add_node.inputs[2])
    scene.node_tree.links.new(rgb_to_bw_node.outputs["Val"], divide_node.inputs[2])
    scene.node_tree.links.new(rgb_to_bw_node.outputs["Val"], shadow_color_correction_node.inputs[0])
    scene.node_tree.links.new(shadow_color_correction_node.outputs["Value"], mask_multiply_node.inputs[0])
    scene.node_tree.links.new(mask_multiply_node.outputs["Value"], set_alpha_node.inputs["Alpha"])
    
    scene.node_tree.links.new(ellipse_mask_node.outputs["Mask"], blur_node.inputs["Image"])
    scene.node_tree.links.new(blur_node.outputs["Image"], mask_multiply_node.inputs[1])
    
    scene.node_tree.links.new(linear_to_srgb_node.outputs["Image"], subtract_node.inputs[1])
    scene.node_tree.links.new(subtract_node.outputs["Image"], add_node.inputs[1])
    scene.node_tree.links.new(add_node.outputs["Image"], divide_node.inputs[1])
    scene.node_tree.links.new(divide_node.outputs["Image"], set_alpha_node.inputs["Image"])
    
    scene.node_tree.links.new(set_alpha_node.outputs["Image"], alpha_convert_node.inputs["Image"])
    scene.node_tree.links.new(alpha_convert_node.outputs["Image"], srgb_to_linear_node.inputs["Image"])
    scene.node_tree.links.new(srgb_to_linear_node.outputs["Image"], alpha_over_node.inputs[1])
    
    scene.node_tree.links.new(alpha_over_node.outputs["Image"], composite_node.inputs["Image"])
    scene.node_tree.links.new(alpha_over_node.outputs["Image"], viewer_node.inputs["Image"])


def create_backdrop(location, scale):
    bm = bmesh.new()
    
    v1 = bm.verts.new((-1,-1,0))
    v2 = bm.verts.new((1,-1,0))
    v3 = bm.verts.new((1,1,0))
    v4 = bm.verts.new((-1,1,0))
    v5 = bm.verts.new((-1,1,1))
    v6 = bm.verts.new((1,1,1))
    
    bm.faces.new((v1,v2,v3,v4))
    bm.faces.new((v6,v5,v4,v3))
    
    mesh = bpy.data.meshes.new("Backdrop")
    obj = bpy.data.objects.new("Backdrop", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm.to_mesh(mesh)
    bm.free()
    
    mod = obj.modifiers.new("Geometry Nodes", "BEVEL")
    mod.width = 0.25
    mod.segments = 64
    
    mat = bpy.data.materials.new(name = "Shadow Only")
    mat.use_nodes = True
    
    shader_node = mat.node_tree.nodes["Principled BSDF"]
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    
    obj.data.polygons.foreach_set("use_smooth",  [True] * len(obj.data.polygons))
    obj.data.update()
    
    obj.location = location
    obj.scale = scale
    
    return obj


def set_resolution(height, crop = None):
    scene = bpy.data.scenes["Scene"]
    scene.render.resolution_x = height // 2 * 3
    scene.render.resolution_y = height
    
    if crop is not None:
        if np.array_equal(np.array(crop), np.array((0,1,0,1))):
            scene.render.use_border = False
            scene.render.use_crop_to_border = False
        else:
            scene.render.use_border = True
            scene.render.use_crop_to_border = True
        bpy.data.scenes["Scene"].render.border_min_x = crop[0]
        bpy.data.scenes["Scene"].render.border_max_x = crop[1]
        bpy.data.scenes["Scene"].render.border_min_y = crop[2]
        bpy.data.scenes["Scene"].render.border_max_y = crop[3]
    

def setup_camera(offset = (0,0,0), distance = 1, angle = (0,0,0), lens = 85, height = 640, crop = None):
    cam_data = bpy.data.cameras.new(name="Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    cam_axis = bpy.data.objects.new(name = "Camera Axis", object_data = None)
    cam_obj.parent = cam_axis
    cam_obj.location = (0,-distance,0)
    cam_obj.rotation_euler = (np.pi/2,0,0)
    cam_axis.location = offset
    cam_axis.rotation_euler = angle 
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.collection.objects.link(cam_axis)
    cam_data.lens = lens
    bpy.data.scenes["Scene"].camera = cam_obj
    
    set_resolution(height, crop)
    
    return (cam_axis, cam_obj)


def setup_lighting(offset = (0,0,0), shifts = (-1,-1,1), energies = (1,1,1), sizes = (1,1,1),
                   horizontal_angles = (-np.pi/4, np.pi/4, np.pi/4), 
                   vertical_angles = (-np.pi/4, -np.pi/4, np.pi/4),
                   types = ("AREA","AREA","POINT"),
                   names = ("Key","Fill","Rim")):
    bpy.data.scenes["Scene"].render.film_transparent = True
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs["Strength"].default_value = 0
    
    lights = []
    for i in range(len(shifts)):
        light = bpy.data.lights.new(name = names[i], type = types[i])
        obj = bpy.data.objects.new(name = names[i], object_data = light)
        axis = bpy.data.objects.new(name = names[i] + " Axis", object_data = None)
        obj.parent = axis
        obj.location = (0,shifts[i],0)
        obj.rotation_euler = (np.pi/2,0,0)
        axis.location = offset
        axis.rotation_euler = (vertical_angles[i],0,horizontal_angles[i])
        light.energy = energies[i]
        if types[i] == "AREA":
            light.shape = "DISK"
            light.size = sizes[i]
        elif types[i] == "POINT":
            light.shadow_soft_size = sizes[i]
        bpy.context.scene.collection.objects.link(obj)
        bpy.context.scene.collection.objects.link(axis)
        lights.append((axis,obj))
    
    return lights


def create_poisson_disk_samples(obj):
    vert_bm = bmesh.new()
    vert_bm.verts.new((0,0,0))
    vert_mesh = bpy.data.meshes.new("Single Vertex")
    vert_obj = bpy.data.objects.new("Single Vertex", vert_mesh)
    vert_bm.to_mesh(vert_mesh)
    vert_bm.free()
    bpy.context.collection.objects.link(vert_obj)
    mod = obj.modifiers.new("Geometry Nodes", "NODES")
    input_node = mod.node_group.nodes["Group Input"]
    output_node = mod.node_group.nodes["Group Output"]
    point_distribute_node = mod.node_group.nodes.new("GeometryNodePointDistribute")
    point_distribute_node.distribute_method = "POISSON"
    point_distribute_node.inputs["Distance Min"].default_value = 0.1
    point_distribute_node.inputs["Density Max"].default_value = 100000
    point_instance_node = mod.node_group.nodes.new("GeometryNodePointInstance")
    point_instance_node.inputs[1].default_value = vert_obj
    make_geometry_real_workaround_node = mod.node_group.nodes.new("GeometryNodeAttributeMath")
    mod.node_group.links.clear()
    mod.node_group.links.new(input_node.outputs["Geometry"], point_distribute_node.inputs["Geometry"])
    mod.node_group.links.new(point_distribute_node.outputs["Geometry"], point_instance_node.inputs["Geometry"])
    mod.node_group.links.new(point_instance_node.outputs["Geometry"], make_geometry_real_workaround_node.inputs["Geometry"])
    mod.node_group.links.new(make_geometry_real_workaround_node.outputs["Geometry"], output_node.inputs["Geometry"])


def export_poisson_disk_samples(obj, file_name):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    sample_obj = obj.evaluated_get(depsgraph)
    samples = np.stack([v.co for v in sample_obj.data.vertices])
    np.savetxt(file_name, samples, delimiter=', ')