import bpy
import bmesh
from functools import partial
import numpy as np
import os
from mathutils import Vector


@partial(np.vectorize, signature = "(n)->()")
def ackley_function(x):
    dimension = x.shape[0]
    a = 20
    b = 0.2
    c = 2 * np.pi
    
    a_exp_term = -a * np.exp(-b * np.sqrt(np.sum(x**2) / dimension))
    exp_cos_term = - np.exp(np.sum(np.cos(c * x) / dimension))
    y = a_exp_term + exp_cos_term + a + np.exp(1.)
    
    return y
    
    
@partial(np.vectorize, signature = "(n)->()")
def levy_function(x):
    dimension = x.shape[0]
    pi = np.pi
    w1 = 1 + (x[0] - 1) / 4.
    y = np.sin(pi * w1)**2
    
    for i in range(dimension - 1):
        wi = 1 + (x[i] - 1) / 4.
        y += (wi - 1)**2 * (1 + 10 * np.sin(pi * wi + 1)**2)
        
    wd = 1 + (x[-1] - 1) / 4.
    y += (wd - 1)**2 * (1 + np.sin(2 * pi * wd)**2)
    
    return y


@partial(np.vectorize, signature = "(n)->()")
def rosenbrock_function(x):
    numerical_stability_factor = 0.01
    
    a = (x[1:] - x[:-1]**2)
    b = (1 - x[:-1])
    y = np.sum(numerical_stability_factor * 100 * a * a + numerical_stability_factor * b * b)
    
    return y


def create_surface(fn, grid_size = 250, x = (-1,1), y = (-1,1), palette_file = None):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments = grid_size, y_segments = grid_size, size = 1)
    
    shift = np.array(((x[1] + x[0])/2, (y[1] + y[0])/2))
    scale = np.array(((x[1] - x[0])/2, (y[1] - y[0])/2))
    
    grid = np.dstack(np.meshgrid(np.linspace(-1,1,grid_size),np.linspace(-1,1,grid_size)))
    log_min = np.min(np.log1p(fn(grid * scale + shift)) / np.log(10))
    log_max = np.max(np.log1p(fn(grid * scale + shift)) / np.log(10))
    
    color_palette = np.vstack((np.genfromtxt(palette_file, delimiter=","), np.ones((1,256))))
    
    @partial(np.vectorize, signature = "(),(n)->()")
    def color(x, palette):
        return np.interp(1 - x, np.linspace(0,1,256), palette) 
    
    color_layer = bm.loops.layers.color.new("color")
    for face in bm.faces:
        for loop in face.loops:
            if loop.vert.co[2] == 0:
                if loop.vert.co[0] > 0.9 and loop.vert.co[1] > 0.9:
                    center = Vector((0.9,0.9,0))
                elif loop.vert.co[0] > 0.9 and loop.vert.co[1] < -0.9:
                    center = Vector((0.9,-0.9,0))
                elif loop.vert.co[0] < -0.9 and loop.vert.co[1] > 0.9:
                    center = Vector((-0.9,0.9,0))
                elif loop.vert.co[0] < -0.9 and loop.vert.co[1] < -0.9:
                    center = Vector((-0.9,-0.9,0))
                else:
                    center = None
                if center is not None:
                    centered = loop.vert.co - center
                    if centered.length > 0.1:
                        loop.vert.co = center + 0.1 * centered.normalized()
            value = fn(np.array(loop.vert.co[:2]) * scale + shift)
            log_value = np.log1p(value) / np.log(10)
            loop.vert.co[2] = value
            loop[color_layer] = color((log_value - log_min) / (log_max - log_min), color_palette)
            
    bm.normal_update()
                
    return bm
    
    


directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings(num_samples = 2048 if bpy.app.background else 128)
(cam_axis, cam_obj) = setup_camera(offset = (0,0,1), distance = 10, angle = (-np.pi/8,0,9*np.pi/8), height = 450, crop = (1/6,5/6,1/6,5/6))
((key_axis,key_obj),(fill_axis,fill_obj),(rim_axis,rim_obj),(lower_fill_axis,lower_fill_obj)) = setup_lighting(
    offset = (0,0,0.5), shifts = (-5,-5,5,5), sizes = (1,5,2,2), energies = (150,125,100,500), 
    horizontal_angles = (5*np.pi/4, -9*np.pi/8, -3*np.pi/4, np.pi/4), vertical_angles = (-np.pi/3, -np.pi/4, np.pi/6, 0),
    names = ("Key","Fill","Rim","Lower Fill"),
    types = ("AREA","AREA","POINT","POINT"))


if bpy.app.background:
    a_bm = create_surface(ackley_function, x = (-2,2), y = (-2,2), palette_file = os.path.join(directory, "col", "viridis.csv"))
    a_obj = add_mesh(a_bm)
    a_obj.scale = (1,1,0.2)
    a_mat = add_vertex_colors(a_obj)
    a_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.625
    lower_fill_obj.data.energy = 500
    bpy.context.scene.render.filepath = os.path.join(directory, "output", "fn_a.png")
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [a_obj], materials = [a_mat])


    l_bm = create_surface(levy_function, x = (-10,10), y = (-10,10), palette_file = os.path.join(directory, "col", "viridis.csv"))
    l_obj = add_mesh(l_bm)
    l_obj.location = (0,0,0.5)
    l_obj.scale = (1,1,0.01)
    l_mat = add_vertex_colors(l_obj)
    l_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.625
    bpy.context.scene.render.filepath = os.path.join(directory, "output", "fn_l.png")
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [l_obj], materials = [l_mat])


    r_bm = create_surface(rosenbrock_function, x = (-2,2), y = (-2,2), palette_file = os.path.join(directory, "col", "viridis.csv"))
    r_obj = add_mesh(r_bm)
    r_obj.location = (0,0,0.625)
    r_obj.scale = (1,1,0.025)
    r_mat = add_vertex_colors(r_obj)
    r_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.625
    bpy.context.scene.render.filepath = os.path.join(directory, "output", "fn_r.png")
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [r_obj], materials = [r_mat])