import eel

import os
import glob
import shutil
import codecs
from OpenGL.GL import *
from OpenGL.WGL import *
from ctypes import *
import numpy
import pyaudio
import array
import re

class FileSystem():
    def __init__(self):
        self.categoryDir = './category'
        self.extension = '.glsl'
        self.defaultSrc = '''vec2 mainSound(int samp, float time){        
  return vec2(sin(6.2831*440.0*time)*exp(-3.0*time));
}
'''
     
        if not os.path.exists(self.categoryDir):
            os.mkdir(self.categoryDir)
        if len(self.listCategory())==0:
            self.newCategory('default')        
                
    def load(self, name):
        src = ''
        if os.path.exists(name):
            f = codecs.open(name, 'r', 'utf-8') 
            src = f.read()
            f.close()
        return src

    def save(self, name, src):
        f = codecs.open(name, 'w', 'utf-8')  
        f.write(src)
        f.close()

    def pathCategory(self, category):
        return self.categoryDir + '/' + category 

    def filenameShader(self, category, shader):
        return self.pathCategory(category) + '/' + shader + self.extension

    def listCategory(self):
        files = glob.glob(self.pathCategory("*"))
        files.sort(key=os.path.getatime, reverse=True)
        return ",".join(list(map(lambda a:os.path.basename(a),files)))

    def listShaders(self, category):
        files = glob.glob(self.filenameShader(category, '*'))
        files.sort(key=os.path.getmtime, reverse=True)
        return ','.join(list(map(lambda a:os.path.basename(a).split('.')[0],files)))
        
    def newShader(self, category):
        name = self.uniqShader(category)
        self.saveShader(category, name, self.defaultSrc)
        return name
    
    def newCategory(self, category):
        if len(category)==0: return 0
        name = self.pathCategory(category)
        if not os.path.exists(name):
            os.mkdir(name)
            self.save(self.filenameShader(category, category), self.defaultSrc)
            return 1
        return 0

    def forkShader(self, category, shader):
        name = self.uniqShader(category, shader)
        self.saveShader(category, name, self.loadShader(category, shader))
        return name

    
    def delShader(self, category, shader):
        ret = 0
        name = self.filenameShader(category, shader)
        if os.path.exists(name): os.remove(name)
        if len(self.listShaders(category))==0:
            ret = 1
            os.rmdir(self.pathCategory(category))
            if len(self.listCategory())==0:
                self.newCategory('default')
        return ret

    def renameCategory(self, old, new):
        if len(new) == 0: return 0
        if os.path.exists(self.pathCategory(new)):
            return 0
        os.rename(self.pathCategory(old), self.pathCategory(new))
        return 1

    def renameShader(self, category, old, new):
        if len(new) == 0: return 0
        if os.path.exists(self.filenameShader(category, new)):
            return 0
        else:
            os.rename(self.filenameShader(category, old), self.filenameShader(category, new))
            return 1
            
    def uniqShader(self, category, shader = '', fork = True):
        if (len(shader) is 0):
            num = 0
            while os.path.exists(self.filenameShader(category, category + "_" + str(num))):
                num += 1
            return category + "_" + str(num)
        else:
            num = 0
            s = "_fork" if fork else "-"
            shader = re.sub(r'_.*[0-9]*', '', shader)
            while os.path.exists(self.filenameShader(category, shader + s + str(num))):
                num += 1
            return shader + s + str(num)            

    def shiftShader(self, old, new, shader):
        name = self.uniqShader(new, shader, False)
        shutil.move(
            self.filenameShader(old, shader),
            self.filenameShader(new, name))
        if len(self.listShaders(old))==0:
            os.rmdir(self.pathCategory(old))
        return name

    def forkShader(self, category, shader):
        srcFilename = self.filenameShader(category, shader)
        name = self.uniqShader(category, shader)
        dstFilename = self.filenameShader(category, name)
        self.save(dstFilename, self.load(srcFilename))
        return name

    def loadShader(self, category, shader):
        filename = self.filenameShader(category, shader)
        return self.load(filename)

    def saveShader(self, category, shader, src):
        filename = self.filenameShader(category, shader)
        self.save(filename, src)


class SoundShader():
    def __init__(self, chunk, rate):
        self.chunk = chunk
        self.rate = rate
        self.channels = 2
        
        self.head ='''
#version 430
out vec2 gain; 
uniform float iFrameCount;
const float iChunk = {0:.1f};
const float iSampleRate = {1:.1f};    
'''.format(self.chunk ,self.rate)

        self.foot ='''
void main() {
    float time = (iChunk * iFrameCount + float(gl_VertexID)) / iSampleRate;
    int samp = int(iFrameCount);
    gain = clamp(mainSound(samp, time), -1.0, 1.0);
}
'''
        # OpenGL Context
        self.hWnd = windll.user32.CreateWindowExA(0,0xC018,0,0,0,0,0,0,0,0,0,0)
        self.hDC = windll.user32.GetDC(self.hWnd)
        pfd = PIXELFORMATDESCRIPTOR(0,1,0,32,0,0,0,0,0,0,0,0,0,0,0,0,0,32,0,0,0,0,0,0,0)
        SetPixelFormat(self.hDC,ChoosePixelFormat(self.hDC, pfd), pfd)
        self.hGLrc = wglCreateContext(self.hDC)
        wglMakeCurrent(self.hDC, self.hGLrc)
        
        # Buffer
        self.samples = (c_float * self.chunk * self.channels)()
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, sizeof(self.samples), None, GL_STATIC_DRAW)
        glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, vbo)
         
        self.alive = False
        self.success = False
        self.program = glCreateProgram()

    def audioData(self, frame_count):
        if self.alive:
            glUniform1f(glGetUniformLocation(self.program, "iFrameCount"), frame_count)
            glEnable(GL_RASTERIZER_DISCARD)
            glBeginTransformFeedback(GL_POINTS)
            glDrawArrays(GL_POINTS, 0, self.chunk)
            glEndTransformFeedback()
            glDisable(GL_RASTERIZER_DISCARD)
            glGetBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(self.samples), byref(self.samples))
        return numpy.frombuffer(self.samples, dtype=numpy.float32)

    def compile(self, src):
        shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(shader, self.head + src + self.foot)
        glCompileShader(shader)
        if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
            self.success = False
            return (glGetShaderInfoLog(shader).decode())
        p = self.program
        self.program = glCreateProgram()
        glAttachShader(self.program, shader)
        glDeleteShader(shader)
        outs = cast((c_char_p*1)(b"gain"), POINTER(POINTER(c_char)))
        glTransformFeedbackVaryings(self.program, 1, outs, GL_INTERLEAVED_ATTRIBS)
        glLinkProgram(self.program)
        glUseProgram(self.program)
        glDeleteProgram(p)
        self.success = True
        return ("Success")

    def close(self):
        wglMakeCurrent(0, 0);
        wglDeleteContext(self.hGLrc);
        windll.user32.ReleaseDC(self.hWnd, self.hDC);
        windll.user32.PostQuitMessage(0);
    
    def trimSize(self, src):
        src = re.compile(r'/\*.*?\*/', re.DOTALL).sub("", src)
        src = re.sub(r"//.*",     "", src)
        src = re.sub(r"\t",      " ", src)
        src = re.sub(r" +",      " ", src)
        src = re.sub(r" *\n *", "\n", src)
        src = re.sub(r"\n+",    "\n", src)    
        src = re.sub(r"^\n",      "", src)
        L = src.split("\n")
        for i in range(len(L)):
            s = L[i]
            if re.search("#", s) != None:
                L[i] = "\n" + L[i] + "\n"
            else:
                s = re.sub(r" *\+ *" ,"+", s)
                s = re.sub(r" *\- *" ,"-", s)
                s = re.sub(r" *\* *" ,"*", s)
                s = re.sub(r" */ *"  ,"/", s)
                s = re.sub(r" *= *"  ,"=", s)
                s = re.sub(r" *< *"  ,"<", s)
                s = re.sub(r" *> *"  ,">", s)
                s = re.sub(r" *& *"  ,"&", s)
                s = re.sub(r" *\| *" ,"|", s)
                s = re.sub(r" *\( *" ,"(", s)
                s = re.sub(r" *\) *" ,")", s)
                s = re.sub(r" *\[ *" ,"[", s)
                s = re.sub(r" *\] *" ,"]", s)
                s = re.sub(r" *{ *"  ,"{", s)
                s = re.sub(r" *} *"  ,"}", s)
                s = re.sub(r" *; *"  ,";", s)
                s = re.sub(r" *, *"  ,",", s)
                L[i] = s
        src = "".join(L)
        src = re.sub(r"\n+", "\n", src)
        src = re.sub(r"^\n", "", src)
        return len(src)
        

class Tick():
    def __init__(self, chunk, rate):
        self.n = 0
        self.chunk = chunk
        self.rate = rate
        self.startN = 0
        self.endN = 1800
        
    def clucN(self, sec):
        return  sec * self.rate / self.chunk
        
    def clucTime(self, n):
        return  n * self.chunk / self.rate
        
    def startTime(self, sec):
        self.startN = self.clucN(sec)
        self.n = max(self.startN, self.n)

    def endTime(self, sec):
        self.endN = self.clucN(sec)
        self.n = min(self.endN, self.n)
        
    def reset(self):
        self.n = self.startN

    def time(self):
        return self.clucTime(self.n)
    
    def tick(self):
        self.n += 1
        if self.endN < self.n:
            self.n = self.startN
        return self.n


@eel.expose
def charSize(src):
    global s
    return s.trimSize(src)

@eel.expose
def compile(src):
    global s
    s.alive = False
    ret = s.compile(src)
    s.alive = True
    return ret

@eel.expose
def success():
    global s
    return s.success

@eel.expose
def listCategory():
    global f
    return f.listCategory()

@eel.expose
def listShaders(category):
    global f
    return f.listShaders(category)

@eel.expose
def newCategory(category):
    global f
    return f.newCategory(category)

@eel.expose
def newShader(category):
    global f
    return f.newShader(category)

@eel.expose
def forkShader(category, shader):
    global f
    return f.forkShader(category, shader)

@eel.expose
def delShader(category, shader):
    global f
    return f.delShader(category, shader)

@eel.expose
def renameCategory(old, new):
    global f
    return f.renameCategory(old, new)

@eel.expose
def renameShader(category, old, new):
    global f
    return f.renameShader(category, old, new)

@eel.expose
def shiftShader(old, new, shader):
    global f
    return f.shiftShader(old, new, shader)

@eel.expose
def loadShader(category, shader):
    global f
    return f.loadShader(category, shader)

@eel.expose
def saveShader(category, shader,src):
    global f
    return f.saveShader(category, shader, src)

@eel.expose
def reset():
    global t
    t.reset()
    
@eel.expose
def startTime(x):
    global t
    t.startTime(x)

@eel.expose
def endTime(x):
    global t
    t.endTime(x)

@eel.expose
def play():
    global s
    s.alive = s.success
    return s.alive

@eel.expose
def stop():
    global s
    s.alive = False

@eel.expose
def close():
    global alive
    alive = False
    
##+++ main +++++++++++++++++

eel.init("web")
eel.start("index.html",port=8002, block=False)

chunk = 2048
rate = 44100
s = SoundShader(chunk, rate)
t = Tick(chunk, rate)
f = FileSystem()

alive = True
eel.data(s.audioData(0).tolist())

p = pyaudio.PyAudio()
stream = p.open(
    format = pyaudio.paFloat32,
    channels = 2,
    rate = s.rate,
    frames_per_buffer = s.chunk,
    output=True,
    input=False
    )
stream.start_stream()
while alive:
    eel.sleep(0.01)
    if s.alive:
        data = s.audioData(t.tick())
        stream.write(array.array('f', data).tobytes())
        eel.data(numpy.hstack((data[::2], data[1::2])).tolist())
        eel.time(t.time())
stream.stop_stream()
s.close()
