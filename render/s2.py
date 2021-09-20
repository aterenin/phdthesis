import bpy
import bmesh
from functools import partial
import numpy as np
import os
from mathutils import Vector


def add_face_colors(obj, data_file, palette_file, bounds = None):
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
    
    obj.data.materials.clear()
    for (idx,color) in enumerate(colors.T):
        mat = bpy.data.materials.new(name = "Face Color %i" % idx)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb_to_linear(color)
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
        obj.data.materials.append(mat)
    
    for (idx,polygon) in enumerate(obj.data.polygons):
        polygon.material_index = idx
        polygon.use_smooth = True
        
    mat = bpy.data.materials.new(name = "Wireframe Color")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0,0,0,1)
    obj.data.materials.append(mat)
    
    mod = obj.modifiers.new("Wireframe", "WIREFRAME")
    mod.use_replace = False
    mod.material_offset = len(obj.data.polygons)
    mod.thickness = 0.005


def create_elliptical_torus(line_thickness = 0.25, vertical_thickness = 1):
    bpy.ops.mesh.primitive_torus_add(major_segments = 256, minor_segments = 64, minor_radius = line_thickness)
    obj = bpy.data.objects["Torus"]
    obj.rotation_euler = (np.pi/2, 0, 0)
    obj.scale = (1,1,vertical_thickness)
    
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(rotation = True, scale = True)
    
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials["Black Surface"])
    
    return obj
    
    
def add_texture(mat,texture_file_path):
    shader_node = mat.node_tree.nodes["Principled BSDF"]
    vertex_color_node = mat.node_tree.nodes["Vertex Color"]
    texture_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    texture_node.image = bpy.data.images.load(texture_file_path)
    mix_node = mat.node_tree.nodes.new("ShaderNodeMixRGB")
    mix_node.blend_type = "MULTIPLY"
    mix_node.inputs["Fac"].default_value = 0.75
    
    mat.node_tree.links.new(vertex_color_node.outputs["Color"], mix_node.inputs["Color1"])
    mat.node_tree.links.new(texture_node.outputs["Color"], mix_node.inputs["Color2"])
    mat.node_tree.links.new(mix_node.outputs["Color"], shader_node.inputs["Base Color"])


def transform_uv_to_mercator(obj):
    for loop in obj.data.loops:
        obj.data.uv_layers.active.data[loop.index].uv[0] = -obj.data.uv_layers.active.data[loop.index].uv[0] + 1.5
    

directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings(num_samples = 2048 if bpy.app.background else 128)
setup_layers()
setup_compositor(mask_center = (0.5,0.3125), mask_size = (0.675,0.325), shadow_color_correction_exponent = 2.75)
(cam_axis, cam_obj) = setup_camera(distance = 9.125, angle = (-np.pi/16, 0, 0), lens = 85, height = 2560, crop = (1/5,9/10,0,10/11))
setup_lighting(shifts = (-10,-10,10), sizes = (9,18,15), energies = (1500,150,1125),
               horizontal_angles = (-np.pi/6, np.pi/3, np.pi/3), vertical_angles = (-np.pi/3, -np.pi/6, np.pi/4))
bm = import_bmesh(os.path.join(directory, "mgp", "s2.obj"))
bd_obj = create_backdrop(location = (0, 0, -1), scale = (5,5,5))
arr_obj = create_vector_arrow()
set_object_collections(backdrop = [bd_obj], instancing = [arr_obj])


if bpy.app.background:
    for file in ["s2_sv1.csv","s2_sv2.csv","s2_sv3.csv","s2_ev.csv","s2_pr.csv"]:
        import_color(bm, color = (31/255, 119/255, 180/255, 1))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        vf_bm = import_vector_field(os.path.join(directory, "mgp", file))
        vf_obj = add_vector_field(vf_bm, arr_obj, scale = 3)
        set_object_collections(object = [obj, vf_obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        set_resolution(480)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj,vf_obj], materials = [mat], modifiers = vf_obj.modifiers)
        
        
    for file in ["s2_xy.csv"]:
        import_color(bm, color = (31/255, 119/255, 180/255, 1))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        vf_bm = import_vector_field(os.path.join(directory, "mgp", file))
        vf_obj = add_vector_field(vf_bm, arr_obj, scale = 3)
        set_object_collections(object = [obj, vf_obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        set_resolution(520)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj,vf_obj], materials = [mat], modifiers = vf_obj.modifiers)
        
        
    for files in [("s2_pm.csv","s2_ps.csv")]:
        import_color(bm, data_file = os.path.join(directory, "mgp", files[1]), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        add_texture(mat, os.path.join(directory, "mgp", "mercator.png"))
        transform_uv_to_mercator(obj)
        vf_bm = import_vector_field(os.path.join(directory, "mgp", files[0]))
        vf_obj = add_vector_field(vf_bm, arr_obj, scale = 0.00375)
        set_object_collections(object = [obj, vf_obj])
        obj.scale = (1,-1,1)
        vf_obj.scale = (1,-1,1)
        obj.rotation_euler = (np.pi, np.pi/12, np.pi/2)
        vf_obj.rotation_euler = (np.pi, np.pi/12, np.pi/2)
        bpy.context.scene.render.filepath = os.path.join(directory, "output", files[0].replace(".csv",".png"))
        set_resolution(560)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj,vf_obj], materials = [mat], modifiers = vf_obj.modifiers)
        
        
    for files in [("s2_obs.csv","s2_pcc.csv","s2_ps.csv")]:
        import_color(bm, data_file = os.path.join(directory, "mgp", files[2]), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        add_texture(mat, os.path.join(directory, "mgp", "mercator.png"))
        transform_uv_to_mercator(obj)
        obs_bm = import_vector_field(os.path.join(directory, "mgp", files[0]))
        cc_bm = import_vector_field(os.path.join(directory, "mgp", files[1]))
        obs_obj = add_vector_field(obs_bm, arr_obj, scale = 0.00375)
        ell_obj = create_elliptical_torus(line_thickness = 0.2, vertical_thickness = 1)
        cc_obj = add_vector_field(cc_bm, ell_obj, scale = 0.01)
        set_object_collections(object = [obj, cc_obj], instancing = [ell_obj])
        obj.scale = (1,-1,1)
        obs_obj.scale = (1,-1,1)
        cc_obj.scale = (1,-1,1)
        obj.rotation_euler = (np.pi, np.pi/12, np.pi/2)
        obs_obj.rotation_euler = (np.pi, np.pi/12, np.pi/2)
        cc_obj.rotation_euler = (np.pi, np.pi/12, np.pi/2)
        vf_mat_orig = arr_obj.data.materials[0]
        vf_mat = bpy.data.materials.new(name = "Gray Surface")
        vf_mat.use_nodes = True
        vf_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb_to_linear((0.5,0.5,0.5,1))
        obs_obj.modifiers["Vector Field"].node_group.nodes["Attribute Combine XYZ"].input_type_x = "FLOAT"
        obs_obj.modifiers["Vector Field"].node_group.nodes["Attribute Combine XYZ"].inputs[2].default_value = 3.5
        obs_obj.modifiers["Vector Field"].node_group.nodes["Attribute Combine XYZ"].input_type_z = "FLOAT"
        obs_obj.modifiers["Vector Field"].node_group.nodes["Attribute Combine XYZ"].inputs[6].default_value = 3.5
        arr_obj.data.materials.clear()
        arr_obj.data.materials.append(vf_mat)
        bpy.context.scene.render.filepath = os.path.join(directory, "output", files[1].replace(".csv",".png"))
        set_resolution(560)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        arr_obj.data.materials.clear()
        arr_obj.data.materials.append(vf_mat_orig)
        cleanup(objects = [obj,ell_obj,obs_obj,cc_obj], materials = [mat,vf_mat], modifiers = [obs_obj.modifiers["Vector Field"], cc_obj.modifiers["Vector Field"]])
        
        
    for file in ["s2_ker.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        obj.rotation_euler[0] = np.pi / 6
        sph_obj = create_dot(location = (0,-1.01 * np.sin(obj.rotation_euler[0]),1.01 * np.cos(obj.rotation_euler[0])), radius = 0.025, color = (0,0,0,1))
        sph_mat = add_vertex_colors(sph_obj)
        set_object_collections(object = [obj, sph_obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        set_resolution(480)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj,sph_obj], materials = [mat,sph_mat])
        

    for file in ["s2_ker.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
        obj.rotation_euler[0] = np.pi / 6
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace("ker.csv","lim.png"))
        set_resolution(375)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
        
        
    for file in ["ico1_ker.csv", "ico2_ker.csv", "ico3_ker.csv"]:
        ico_bm = import_bmesh(os.path.join(directory, "ggp", file.replace("_ker.csv",".obj")))
        obj = add_mesh(ico_bm)
        add_face_colors(obj, data_file = os.path.join(directory, "ggp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj.rotation_euler[0] = np.pi / 6
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        set_resolution(375)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = obj.data.materials, modifiers = obj.modifiers)
        
        
    for file in ["s2_ex.csv","s2_ey.csv","s2_ez.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(object = [obj])
        set_resolution(230)
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
        
        
    for color in [(31/255, 119/255, 180/255, 1)]:
        import_color(bm, color = color)
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(object = [obj])
        orig_camera_location = np.array(cam_obj.location)
        orig_camera_angle = np.array(cam_axis.rotation_euler)
        cam_obj.location = (0, -9.25, 0)
        cam_axis.rotation_euler = (-5*np.pi/36, 0, 0)
        orig_mask_y = bpy.data.scenes["Scene"].node_tree.nodes["Ellipse Mask"].y
        orig_mask_height = bpy.data.scenes["Scene"].node_tree.nodes["Ellipse Mask"].height
        bpy.data.scenes["Scene"].node_tree.nodes["Ellipse Mask"].y = 0.3375
        bpy.data.scenes["Scene"].node_tree.nodes["Ellipse Mask"].height = 0.3875
        bpy.context.scene.render.filepath = os.path.join(directory, "output", "s2.png")
        set_resolution(480)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cam_obj.location = orig_camera_location
        cam_axis.rotation_euler = orig_camera_angle
        bpy.data.scenes["Scene"].node_tree.nodes["Ellipse Mask"].y = orig_mask_y
        bpy.data.scenes["Scene"].node_tree.nodes["Ellipse Mask"].height = orig_mask_height
        cleanup(objects = [obj], materials = [mat])
    

    for file in ["s2_a.csv","s2_b.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(object = [obj])
        set_resolution(245)
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
     
    
    for file in ["s2_x.csv","s2_y.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "plasma.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(object = [obj])
        set_resolution(245)
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
        
        
    for (files,palette_file) in [(("s2_va.csv","s2_vb.csv"),"viridis.csv"),(("s2_vx.csv","s2_vy.csv"),"plasma.csv")]:
        import_color(bm, color = (31/255, 119/255, 180/255, 1))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        color_palette = np.genfromtxt(os.path.join(directory, "col", palette_file), delimiter=",")
        color = srgb_to_linear(color_palette[:,3*color_palette.shape[1]//4])
        original_shader_node = arr_obj.data.materials["Black Surface"].node_tree.nodes["Principled BSDF"]
        replacement_shader_node = arr_obj.data.materials["Black Surface"].node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        replacement_shader_node.inputs["Base Color"].default_value = np.append(color,1)
        arr_obj.data.materials["Black Surface"].node_tree.links.new(replacement_shader_node.outputs["BSDF"], arr_obj.data.materials[0].node_tree.nodes["Material Output"].inputs["Surface"])
        vf_x_bm = import_vector_field(os.path.join(directory, "mgp", files[0]))
        vf_x_obj = add_vector_field(vf_x_bm, arr_obj, scale = 0.05)
        vf_y_bm = import_vector_field(os.path.join(directory, "mgp", files[1]))
        vf_y_obj = add_vector_field(vf_y_bm, arr_obj, scale = 0.05)
        sph_obj = create_dot()
        sph_obj.data.materials.clear()
        sph_obj.data.materials.append(arr_obj.data.materials["Black Surface"])
        vf_sph_obj = add_vector_field(vf_x_bm, sph_obj, scale = 0.04)
        set_object_collections(object = [obj, vf_x_obj,vf_y_obj,vf_sph_obj], instancing=[sph_obj])
        set_resolution(245)
        bpy.context.scene.render.filepath = os.path.join(directory, "output", files[0].replace(".csv",files[1].replace("s2_v","")).replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        arr_obj.data.materials[0].node_tree.nodes.remove(replacement_shader_node)
        arr_obj.data.materials["Black Surface"].node_tree.links.new(original_shader_node.outputs["BSDF"], arr_obj.data.materials[0].node_tree.nodes["Material Output"].inputs["Surface"])
        cleanup(objects = [obj,vf_x_obj,vf_y_obj,sph_obj,vf_sph_obj], materials = [mat], modifiers = [vf_x_obj.modifiers["Vector Field"],vf_y_obj.modifiers["Vector Field"],vf_sph_obj.modifiers["Vector Field"]])
    
    
    for file in ["s2_e11.csv","s2_e109.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        obj.rotation_euler[0] = -np.pi / 4
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        set_resolution(320)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
        
