import math
import numpy
#import cyglfw3 as glfw
import glfw
import random
import ctypes
import glm
import pyassimp
import pyassimp.postprocess
import OpenGL.GL as gl 
import OpenGL.GL.shaders as shaders
import pywavefront
import pygame


# initialize glfw

glfw.init()

''' declaración de todas las variables '''

#matrices 
model = glm.mat4(1) 
view = glm.mat4(1)
projection = glm.perspective(glm.radians(45), 800/600, 0.1, 100.0)

#vector para la luz
lighting = glm.vec3(-10,20,30)

#variables para el cambio de texturas
ogTexture = True #para el cambio de las texturas, primero se cargara la original
newTexture = ""    #la textura a la cual se desea cambiar
#variables para la rotación y zoom 
camerai = glm.vec3(0,0,10)
camera = glm.vec3(0,0,10)
center = glm.vec3(0,0,0)
up = glm.vec3(0, 1, 0)
camera_speedz = 5
camera_speedxy = 0.5
radio = camera.z
pitch = 0 #angulo que se usa para rotar el objeto respecto al eje x
yaw = 0 #angulo que se usa para rotar el objeto respecto al eje y
roll = 0 #angulo que se usa para rotar el objeto respecto al eje z
axe ="" #eje sobre el cual se desea realizar el zoom
rotate = False
zoom = False
texturas = False

#path para la carpeta del proyecto 
fullPath = "/Users/polaris/Documents/5/GRAFICAS/proyecto2/"


# this makes opengl work on mac (https://developer.apple.com/library/content/documentation/GraphicsImaging/Conceptual/OpenGL-MacProgGuide/UpdatinganApplicationtoSupportOpenGL3/UpdatinganApplicationtoSupportOpenGL3.html)
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

window = glfw.create_window(800, 600, 'Building', None, None)
glfw.make_context_current(window)

# initialize shaders

vertex_shader = """
#version 330
layout (location = 0) in vec4 position;
layout (location = 1) in vec4 normal;
layout (location = 2) in vec2 texcoords;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

uniform vec4 color;
uniform vec4 light;

out vec4 vertexColor;
out vec2 vertexTexcoords;

void main()
{
    float intensity = dot(normal, normalize(light - position))*2;

    gl_Position = projection * view * model * position;
    vertexColor = color * intensity;
    vertexTexcoords = texcoords;
}

"""

fragment_shader = """
#version 330
layout (location = 0) out vec4 diffuseColor;

in vec4 vertexColor;
in vec2 vertexTexcoords;

uniform sampler2D tex;

void main()
{
    diffuseColor = vertexColor * texture(tex, vertexTexcoords);
}
"""


# initialize vertex data

vertex_data = numpy.array([
     0.5,  0.5, 0,   1, 0, 0,    1, 1,
     0.5, -0.5, 0,   0, 1, 0,    1, 0,
    -0.5, -0.5, 0,   0, 0, 1,    0, 0,
    -0.5,  0.5, 0,   1, 1, 0,    0, 1  
], dtype=numpy.float32)

index_data = numpy.array([
    0, 1, 3, 
    1, 2, 3
], dtype=numpy.uint32)

vertex_array_object = gl.glGenVertexArrays(1)
gl.glBindVertexArray(vertex_array_object)

vertex_buffer_object = gl.glGenBuffers(1)
gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertex_buffer_object)
gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)

element_buffer_object = gl.glGenBuffers(1)
gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, element_buffer_object)
gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, gl.GL_STATIC_DRAW)

gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, False, 8 * 4, ctypes.c_void_p(0))
gl.glEnableVertexAttribArray(0)
gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, False, 8 * 4, ctypes.c_void_p(3 * 4))
gl.glEnableVertexAttribArray(1)
gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, False, 8 * 4, ctypes.c_void_p(6 * 4))
gl.glEnableVertexAttribArray(2)
    

# glfw requires shaders to be compiled after buffer binding

shader = shaders.compileProgram(
    shaders.compileShader(vertex_shader, gl.GL_VERTEX_SHADER),
    shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER)
)
gl.glUseProgram(shader)
gl.glClearColor(0.5, 0.5, 0.5, 1.0)

gl.glViewport(0, 0, 800, 600)
#cargar el obj
scene = pyassimp.load(fullPath+ "coliseo/coliseo.obj")

# glfw requires shaders to be compiled after buffer binding
#NOTA PARA MAC use program shader tiene que estar despues de los buffers

def getTexture(mesh):
    
    if ogTexture == True:
        material = dict(mesh.material.properties.items())
        texture = material['file'][0:]
        path = fullPath+ "/coliseo/"+texture
    else:
        path = fullPath+ "textures/"+newTexture
    return path


def glize(node):
    model = node.transformation.astype(numpy.float32)

    gl.glUniformMatrix4fv(
    gl.glGetUniformLocation(shader, "model"), 1 , gl.GL_FALSE, 
    model
    )
    gl.glUniformMatrix4fv(
        gl.glGetUniformLocation(shader, "view"), 1 , gl.GL_FALSE, 
        glm.value_ptr(view)
    )
    gl.glUniformMatrix4fv(
        gl.glGetUniformLocation(shader, "projection"), 1 , gl.GL_FALSE, 
        glm.value_ptr(projection)
    )

    for mesh in node.meshes:
        #assert False , texture #prueba para ver el nombre de la textura
        texture_surface =  pygame.image.load(getTexture(mesh))
        texture_data = pygame.image.tostring(texture_surface, "RGB", 1)
        width = texture_surface.get_width()
        height = texture_surface.get_height()

        texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, texture_data)
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

        vertex_data = numpy.hstack((
            numpy.array(mesh.vertices, dtype=numpy.float32),
            numpy.array(mesh.normals, dtype=numpy.float32),
            numpy.array(mesh.texturecoords[0], dtype=numpy.float32)
        ))

        index_data = numpy.hstack(
            numpy.array(mesh.faces, dtype=numpy.int32)
        )

        vertex_buffer_object = gl.glGenVertexArrays(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertex_buffer_object)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)

        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, False, 9 * 4, None)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, False, 9 * 4, ctypes.c_void_p(3 * 4))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, False, 9 * 4, ctypes.c_void_p(6 * 4))
        gl.glEnableVertexAttribArray(2)


        element_buffer_object = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, element_buffer_object)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, gl.GL_STATIC_DRAW)

        diffuse = mesh.material.properties["diffuse"]
        gl.glUniform4f(
            gl.glGetUniformLocation(shader, "color"),
            *diffuse,
            1
        )

        gl.glUniform4f(
            gl.glGetUniformLocation(shader, "light"), 
            int(lighting.x), int(lighting.y), int(lighting.z), 1
        )
        gl.glDrawElements(gl.GL_TRIANGLES, len(index_data), gl.GL_UNSIGNED_INT, None)


    for child in node.children:
        glize(child)        


def camera_handle(ventana, key, scancode, action, mods):
    global pitch, yaw, roll, rotate, zoom, axe, camera, texturas, ogTexture, newTexture, view
    #si se presiona una tecla
    if action == glfw.PRESS:
        #para rotar el objeto, se debera presionar la tecla R antes
        if key == glfw.KEY_R:
            camera = camerai
            center.x, center.y, center.z = 0,0,0
            rotate = True
            zoom = False
            texturas = False
            axe =''
        #si se desea mover en un eje estatico (zoom, no rotar), presionar la barra espaciadora antes
        if key == glfw.KEY_SPACE:
            rotate = False
            zoom = True
            texturas = False
            axe =''
        if key == glfw.KEY_T:
            rotate = False
            zoom = False
            texturas = True
            axe =''
        #para rotar el objeto
        if rotate == True:
            #definir el eje sobre el cual se desea rotar
            if key == glfw.KEY_X:
                camera.x, camera.y, camera.z = camerai.x, camerai.y, camerai.z
                center.x, center.y, center.z = 0,0,0
                pitch,yaw, roll = 0,0,0
                view = glm.lookAt(camerai, glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))
                axe = 'X'
            if key == glfw.KEY_Y:
                axe = 'Y'
                camera.x, camera.y, camera.z = camerai.x, camerai.y, camerai.z
                center.x, center.y, center.z = 0,0,0
                pitch,yaw, roll = 0,0,0
                view = glm.lookAt(camerai, glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))
            if key == glfw.KEY_Z:
                axe = 'Z'
                camera.x, camera.y, camera.z = camerai.x, camerai.y, camerai.z
                center.x, center.y, center.z = 0,0,0
                pitch,yaw, roll = 0,0,0
                view = glm.lookAt(camerai, glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))
            #rotar respecto al eje X
            if key == glfw.KEY_LEFT and axe == 'X':
                pitch += 0.3
                camera.y = math.sin(pitch) * radio
                camera.z = math.cos(pitch) * radio
            if key == glfw.KEY_RIGHT and axe == 'X':
                pitch -= 0.3
                camera.y = math.sin(pitch) * radio
                camera.z = math.cos(pitch) * radio
            #rotar respecto al eje Y
            if key == glfw.KEY_LEFT and axe == 'Y':
                yaw += 0.3
                camera.x = math.sin(yaw) * radio
                camera.z = math.cos(yaw) * radio
            if key == glfw.KEY_RIGHT and axe == 'Y':
                yaw -= 0.3
                camera.x = math.sin(yaw) * radio
                camera.z = math.cos(yaw) * radio
            #rotar respecto al eje Z
            if key == glfw.KEY_LEFT and axe == 'Z':
                roll += 0.3
                up.y = math.sin(roll) * radio
                up.x = math.cos(roll) * radio
            if key == glfw.KEY_RIGHT and axe == 'Z':
                roll -= 0.3
                up.y = math.sin(roll) * radio
                up.x = math.cos(roll) * radio
        if zoom == True:
            #definir el eje sobre el cual se desea movilizar
            if key == glfw.KEY_X:
                axe = 'X'
                camera = camerai
                center.x,center.y,center.z = 0,0,0
            if key == glfw.KEY_Y:
                axe = 'Y'
                camera = camerai
                center.x,center.y,center.z = 0,0,0
            if key == glfw.KEY_Z:
                axe = 'Z'
                camera = camerai
                center.x,center.y,center.z = 0,0,0
            #moverse en el eje x
            if key == glfw.KEY_UP and axe == 'X':
                camera.x += camera_speedxy
                center.x += camera_speedxy
                if camera.x >= 2:
                    camera.x = 2
            if key == glfw.KEY_DOWN and axe == 'X':
                camera.x -= camera_speedxy
                center.x -= camera_speedxy
                if camera.x <= -5:
                    camera.x = -5
            #moverse en el eje y
            if key == glfw.KEY_UP and axe == 'Y':
                camera.y += camera_speedxy
                center.y += camera_speedxy
                if camera.y >= 4:
                    camera.y = 4
            if key == glfw.KEY_DOWN and axe == 'Y':
                camera.y -= camera_speedxy
                center.y -= camera_speedxy
                if camera.y <= -3:
                    camera.y = -3
            #moverse en el eje z
            if key == glfw.KEY_UP and axe == 'Z':
                camera.z -= camera_speedz
                center.z -= camera_speedz
                if camera.z <= 7:
                    camera.z = 7
            if key == glfw.KEY_DOWN and axe == 'Z':
                camera.z += camera_speedz
                center.z += camera_speedz
                if camera.z >= 40:
                    camera.z = 40
        if texturas == True:
            if key == glfw.KEY_0:
                ogTexture = True
            if key == glfw.KEY_1:
                ogTexture = False
                newTexture = "polka.jpg"
            if key == glfw.KEY_2:
                ogTexture = False
                newTexture = "grunge_wall.jpg"
            if key == glfw.KEY_3:
                ogTexture = False
                newTexture = "old_rock.jpg"
            if key == glfw.KEY_4:
                ogTexture = False
                newTexture = "solar.jpg"

while not glfw.window_should_close(window):
	# Enable key events
    glfw.set_input_mode(window,glfw.STICKY_KEYS,gl.GL_TRUE) 
	# Enable key event callback
    glfw.set_key_callback(window,camera_handle)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT)

    gl.glUseProgram(shader)
    view = glm.lookAt(camera, center, up)

    glize(scene.rootnode)

    glfw.swap_buffers(window)
    glfw.poll_events()

#cerrar y eliminar todo para un cierre correcto
gl.glDeleteBuffers(1, [vertex_buffer_object])
gl.glDeleteBuffers(1, [element_buffer_object])
gl.glDeleteProgram(shader)
gl.glDeleteVertexArrays(1, [vertex_array_object])

glfw.terminate()
