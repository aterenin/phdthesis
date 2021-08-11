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


def import_color(bm, data_file, palette_file, bounds = None, index = None):
    data = np.genfromtxt(data_file, delimiter=",")
    if index is not None:
        data = data[index,:]
    if bounds is None:
        min = data.min()
        max = data.max()
    else:
        (min,max) = bounds
    data_std = (data - min) / (max - min)
    color_palette = np.genfromtxt(palette_file, delimiter=",")
    colors = np.vstack((
        np.interp(data_std, np.linspace(0,1,256), color_palette[0,:]),
        np.interp(data_std, np.linspace(0,1,256), color_palette[1,:]),
        np.interp(data_std, np.linspace(0,1,256), color_palette[2,:]),
    ))
    
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


def create_voxel_remesh(bm):
    mesh = bpy.data.meshes.new("Mesh")
    obj = bpy.data.objects.new("Mesh", mesh)
    bpy.context.collection.objects.link(obj)
    bm.to_mesh(mesh)
    
    obj.data.remesh_mode = "VOXEL"
    obj.data.remesh_voxel_size = 0.0005
    
    bpy.ops.object.select_all(action = "DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.voxel_remesh()
    
    vox_bm = bmesh.new()
    vox_bm.from_mesh(mesh)
    
    bpy.data.objects.remove(obj, do_unlink = True)
    bpy.data.meshes.remove(mesh, do_unlink = True)
    
    return vox_bm


def transfer_vertex_colors_to_voxel_remesh(obj, bm):
    temp_mesh = bpy.data.meshes.new("Temp")
    temp_obj = bpy.data.objects.new("Temp", temp_mesh)
    bpy.context.collection.objects.link(temp_obj)
    bm.to_mesh(temp_mesh)
    
    bpy.ops.object.select_all(action = "DESELECT")
    temp_obj.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = temp_obj
    bpy.ops.object.data_transfer(data_type = "VCOL")
    
    bpy.data.objects.remove(temp_obj, do_unlink = True)
    bpy.data.meshes.remove(temp_mesh, do_unlink = True)


def subdivide_near_data_points(obj, points_file, radius=0.003):
    points = np.genfromtxt(points_file, delimiter=",", dtype=int)
    mesh = obj.data
    
    bpy.ops.object.select_all(action = "DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bm.verts.ensure_lookup_table()
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]
            for i in points:
                if (vert.co - bm.verts[i].co).length < radius:
                    vert.select = True
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts = 2)
    bpy.ops.object.editmode_toggle()
    

def import_data_points_color(obj, bm, points_file, radius = 0.002):
    points = np.genfromtxt(points_file, delimiter=",", dtype=int)
    mesh = obj.data
    
    bm.verts.ensure_lookup_table()
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]
            for i in points:
                if (vert.co - bm.verts[i].co).length < radius:
                    mesh.vertex_colors["Col"].data[loop_idx].color = (0,0,0,1)


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





directory = os.getcwd()
reset_scene()
set_renderer_settings()
setup_camera(location = (0.005,-0.375,0.195), angle = (np.pi/2 - np.pi/16, 0, 0), lens = 60)
setup_lighting(angle = (np.pi/6, 0, 0), energy = 10)
setup_background(energy = 10)
bm = import_bmesh(os.path.join(directory, "mgp", "dr.obj"))
r_bm = create_voxel_remesh(bm)
sd_obj = setup_shadow_disk(location = (0.005, 0.05, 0.053), scale = (0.12, 0.09, 1))





for file in ("dr_ker.csv",):
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
    obj = add_mesh(r_bm)
    mat = add_vertex_colors(obj)
    transfer_vertex_colors_to_voxel_remesh(obj, bm)
    obj.rotation_euler = (np.pi / 2, 0, 0)
    bm.verts.ensure_lookup_table()
    sph_location = bm.verts[0].co + 0.001 * bm.verts[0].normal
    sph_obj = create_dot(location = (sph_location[0],sph_location[2],sph_location[1]), radius = 0.002, color = (214/255,39/255,40/255,1))
    sph_mat = add_vertex_colors(sph_obj)
    sph_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)
    bpy.data.materials.remove(sph_mat, do_unlink = True)
    bpy.data.objects.remove(sph_obj, do_unlink = True)


for file in ("dr_gt.csv","dr_m.csv","dr_fn.csv"):
    index = 0 if file == "dr_fn.csv" else None
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_plasma.csv"), index = index, bounds = (-2,2))
    obj = add_mesh(r_bm)
    mat = add_vertex_colors(obj)
    transfer_vertex_colors_to_voxel_remesh(obj, bm)
    subdivide_near_data_points(obj, os.path.join(directory, "mgp", "dr_loc.csv"))
    import_data_points_color(obj, bm, os.path.join(directory, "mgp", "dr_loc.csv"))
    obj.rotation_euler = (np.pi / 2, 0, 0)
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)


for file in ("dr_std.csv",):
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
    obj = add_mesh(r_bm)
    mat = add_vertex_colors(obj)
    transfer_vertex_colors_to_voxel_remesh(obj, bm)
    subdivide_near_data_points(obj, os.path.join(directory, "mgp", "dr_loc.csv"))
    import_data_points_color(obj, bm, os.path.join(directory, "mgp", "dr_loc.csv"))
    obj.rotation_euler = (np.pi / 2, 0, 0)
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    bpy.data.materials.remove(mat, do_unlink = True)
    bpy.data.objects.remove(obj, do_unlink = True)


