import bpy
import bmesh
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


def set_renderer_settings():
    bpy.data.scenes["Scene"].render.engine = "CYCLES"
    bpy.data.scenes["Scene"].cycles.device = "GPU"
    bpy.data.scenes["Scene"].cycles.use_denoising = True
    bpy.data.scenes["Scene"].cycles.use_preview_denoising = True


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


def import_color(bm, data_file, palette_file):
    if data_file is not None:
        data = np.genfromtxt(data_file, delimiter=",")
        data_std = (data - data.min()) / (data.max() - data.min())
        color_palette = np.genfromtxt(palette_file, delimiter=",")
        colors = np.vstack((
            np.interp(data_std, np.linspace(0,1,256), color_palette[0,:]),
            np.interp(data_std, np.linspace(0,1,256), color_palette[1,:]),
            np.interp(data_std, np.linspace(0,1,256), color_palette[2,:]),
        ))
    else:
        color_palette = np.genfromtxt(palette_file, delimiter=",")
        colors = np.repeat(color_palette[:,128, np.newaxis], len(bm.verts), axis=-1)
    
    if bm.loops.layers.color.active is not None:
        bm.loops.layers.color.remove(bm.loops.layers.color.active)

    color_layer = bm.loops.layers.color.new("color")
    for face in bm.faces:
        for loop in face.loops:
            loop[color_layer] = colors[:,loop.vert.index].tolist() + [1]


def add_mesh(bm):
    mesh = bpy.data.meshes.new("Mesh")
    obj = bpy.data.objects.new("Mesh", mesh)
    bpy.context.collection.objects.link(obj)
    bm.to_mesh(mesh)

    return obj
    

def add_vertex_colors(obj):
    mat = bpy.data.materials.new(name = "Surface Color")
    mat.use_nodes = True
    vertex_color_node = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    shader_node = mat.node_tree.nodes["Principled BSDF"]
    mat.node_tree.links.new(vertex_color_node.outputs["Color"], shader_node.inputs["Base Color"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    obj.data.polygons.foreach_set("use_smooth",  [True] * len(obj.data.polygons))
    obj.data.update()
    
    return mat


def import_vector_field(vf_file):
    vector_field = np.genfromtxt(vf_file, delimiter=",")

    bm = bmesh.new()
    arrow_layer = bm.verts.layers.float_vector.new("arrow")
    for row in vector_field:
        vert = bm.verts.new(row[0:3])
        vert[arrow_layer] = row[3:6]

    return bm


def add_vector_field(vec_bm, arr_obj, scale = 1):
    vf_mesh = bpy.data.meshes.new("Vector Field")
    vf_obj = bpy.data.objects.new("Vector Field", vf_mesh)
    vec_bm.to_mesh(vf_mesh)
    bpy.data.collections["Collection"].objects.link(vf_obj)

    mod = vf_obj.modifiers.new("Vector Field", "NODES")
    input_node = mod.node_group.nodes["Group Input"]
    output_node = mod.node_group.nodes["Group Output"]
    attribute_length_node = mod.node_group.nodes.new("GeometryNodeAttributeVectorMath")
    attribute_length_node.operation = "LENGTH"
    attribute_length_node.inputs["A"].default_value = "arrow"
    attribute_length_node.inputs["Result"].default_value = "length"
    length_point_scale_node = mod.node_group.nodes.new("GeometryNodePointScale")
    length_point_scale_node.input_type = "ATTRIBUTE"
    length_point_scale_node.inputs["Factor"].default_value = "length"
    constant_point_scale_node  = mod.node_group.nodes.new("GeometryNodePointScale")
    constant_point_scale_node.input_type = "FLOAT"
    constant_point_scale_node.inputs[3].default_value = scale
    align_rotation_node = mod.node_group.nodes.new("GeometryNodeAlignRotationToVector")
    align_rotation_node.axis = "Y"
    align_rotation_node.input_type_vector = "ATTRIBUTE"
    align_rotation_node.inputs["Vector"].default_value = "arrow"
    point_instance_node = mod.node_group.nodes.new("GeometryNodePointInstance")
    point_instance_node.inputs["Object"].default_value = arr_obj

    mod.node_group.links.clear()
    mod.node_group.links.new(input_node.outputs["Geometry"], attribute_length_node.inputs["Geometry"])
    mod.node_group.links.new(attribute_length_node.outputs["Geometry"], length_point_scale_node.inputs["Geometry"])
    mod.node_group.links.new(length_point_scale_node.outputs["Geometry"], constant_point_scale_node.inputs["Geometry"])
    mod.node_group.links.new(constant_point_scale_node.outputs["Geometry"], align_rotation_node.inputs["Geometry"])
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
    bpy.data.collections["Collection"].objects.link(obj)

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


def create_dot(location, radius, color):
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


def setup_shadow_disk(location, scale):
    bm = bmesh.new()
    inner_verts = bmesh.ops.create_circle(bm, radius=1.0, segments=256)["verts"]
    bmesh.ops.holes_fill(bm, edges=bm.edges)
    outer_verts = bmesh.ops.create_circle(bm, radius=1.1, segments=256)["verts"]
    bmesh.ops.bridge_loops(bm, edges=bm.edges)

    alpha_layer = bm.loops.layers.color.new("alpha")
    for face in bm.faces:
        for loop in face.loops:
            if loop.vert in inner_verts:
                loop[alpha_layer] = (0.8,0.8,0.8,1)
            elif loop.vert in outer_verts:
                loop[alpha_layer] = (0.8,0.8,0.8,0)

    mesh = bpy.data.meshes.new("Shadow Disk")
    obj = bpy.data.objects.new("Shadow Disk", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm.to_mesh(mesh)
    bm.free()
    
    mat = bpy.data.materials.new(name = "Shadow Disk Fade")
    mat.use_nodes = True
    vertex_color_node = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    multiply_node =  mat.node_tree.nodes.new("ShaderNodeMath")
    multiply_node.operation = "MULTIPLY"
    multiply_node.inputs[1].default_value = 0.25
    shader_node = mat.node_tree.nodes["Principled BSDF"]
    mat.node_tree.links.new(vertex_color_node.outputs["Alpha"], multiply_node.inputs[0])
    mat.node_tree.links.new(multiply_node.outputs["Value"], shader_node.inputs["Alpha"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.cycles.is_shadow_catcher = True
    
    obj.location = location
    obj.scale = scale
    
    return obj


def setup_camera(location, angle, lens):
    cam_data = bpy.data.cameras.new(name="Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = location
    cam_obj.rotation_euler = angle 
    cam_data.lens = lens
    scene = bpy.data.scenes["Scene"]
    scene.camera = cam_obj
    scene.render.resolution_x = scene.render.resolution_y


def setup_lighting(angle, energy = 10):
    light_data = bpy.data.lights.new(name="Sun", type="SUN")
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.rotation_euler = angle
    light_data.energy = energy


def setup_background(energy = 1):
    bpy.data.scenes["Scene"].render.film_transparent = True
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs["Strength"].default_value = energy


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





directory = os.getcwd()
reset_scene()
set_renderer_settings()
setup_camera(location = (0,-4.25,0.75), angle = (np.pi/2 - np.pi/16, 0, 0), lens = 60)
setup_lighting(angle = (np.pi/6, 0, 0), energy = 10)
setup_background(energy = 10)
bm = import_bmesh(os.path.join(directory, "mgp", "sph.obj"))
sd_obj = setup_shadow_disk(location = (0, 0.6, -1), scale = (1.05, 1.25, 1))
arr_obj = create_vector_arrow()





for file in ("sph_a.csv", "sph_b.csv","sph_ex.csv","sph_ey.csv","sph_ez.csv"):
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
    obj = add_mesh(bm)
    mat = add_vertex_colors(obj)
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)
    
    
for file in ("sph_e11.csv","sph_e89.csv",):
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
    obj = add_mesh(bm)
    mat = add_vertex_colors(obj)
    obj.rotation_euler[0] = -np.pi / 4
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)


for file in ("sph_ker.csv",):
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
    obj = add_mesh(bm)
    mat = add_vertex_colors(obj)
    obj.rotation_euler[0] = np.pi / 6
    sph_obj = create_dot(location = (0,-1.01 * np.sin(obj.rotation_euler[0]),1.01 * np.cos(obj.rotation_euler[0])), radius = 0.025, color = (214/255,39/255,40/255,1))
    sph_mat = add_vertex_colors(sph_obj)
    sph_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)
    bpy.data.materials.remove(sph_mat, do_unlink = True)
    bpy.data.objects.remove(sph_obj, do_unlink = True)


for file in ("sph_x.csv","sph_y.csv"):
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_plasma.csv"))
    obj = add_mesh(bm)
    mat = add_vertex_colors(obj)
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)


for file in ("sph_ev.csv","sph_pr.csv","sph_xy.csv"):
    import_color(bm, None, os.path.join(directory, "mgp", "col_viridis.csv"))
    obj = add_mesh(bm)
    mat = add_vertex_colors(obj)
    vf_bm = import_vector_field(os.path.join(directory, "mgp", file))
    vf_obj = add_vector_field(vf_bm, arr_obj, scale = 3.5)
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)
    bpy.data.objects.remove(vf_obj, do_unlink = True)