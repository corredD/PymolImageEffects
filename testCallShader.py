# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 13:38:08 2017

@author: ludov
"""
import os
try :
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.arrays import vbo
    from OpenGL.GL import shaders
except:
    from pymol.opengl.gl import *
from pymol.callback import Callback
from pymol.wizard import Wizard
from pymol import cmd
import numpy as np

cmd.reinitialize()
#cmd.set("auto_show_classified","0")
cmd.fetch("4xfx", async=0)
cmd.show_as("surface","polymer")
cmd.color("grey70","all")


class Parameters(Wizard):

    def __init__(self,*arg,**kw):
        _self = kw.get('_self',cmd)
        Wizard.__init__(self,_self)
        self.message = []
        for a in arg:
            if not isinstance(a,types.ListType):
                self.message.append(a)
            else:
                self.message.extend(a)
        for a in self.message:
            print " " + _nuke_color_re.sub('',a)
        self.dismiss = int(kw.get("dismiss",1))

        self.n_cap_name = {
            '1.0' : 'Open',
            'posi' : 'NH3+',
            'acet' : 'Acetyl',
            }
        self.n_caps = [ 'none', 'posi', 'acet' ]
        self.ssao = kw['ssao']
#        self.panel_setup=[]
#        self.panel_setup.append([ 1, 'Parameters', '' ])
        for k in self.ssao.SSAO_OPTIONS:
            self.menu[k]=[]
            mini = self.ssao.SSAO_OPTIONS[k][1]
            maxi = self.ssao.SSAO_OPTIONS[k][2]
#            self.panel_setup.append([ 3, "%s: %3.1f"%(k,self.ssao.SSAO_OPTIONS[k][0]), k ])
            if self.ssao.SSAO_OPTIONS[k][3] == "int" and maxi == 1:
                self.menu[k].append([1, 'true','cmd.get_wizard().set_options("%s",1)'%k])
                self.menu[k].append([1, 'false','cmd.get_wizard().set_options("%s",0)'%k])
                if mini == -1 :
                     self.menu[k].append([1, 'disable','cmd.get_wizard().set_options("%s",-1)'%k])
            else :
                for i in range(6):
                    v = mini+((maxi-mini)*(i/5.0))
                    self.menu[k].append([1, '%f'%float(v),'cmd.get_wizard().set_options("%s",%f)'%(k,float(v))])

    def do_scene(self):
        self.cmd.dirty_wizard()

    def do_frame(self,frame):
        self.cmd.dirty_wizard()

    def do_state(self,state):
        self.cmd.dirty_wizard()

    def get_prompt(self):
        self.prompt = self.message
        return self.prompt

    def setssao_only(self):
        if self.ssao.SSAO_OPTIONS['only_ssao'][0] == 1:
            self.ssao.SSAO_OPTIONS['only_ssao'][0]=0
        else :
            self.ssao.SSAO_OPTIONS['only_ssao'][0]=1

    def setonly_depth(self):
        if self.ssao.SSAO_OPTIONS['only_depth'][0] == 1:
            self.ssao.SSAO_OPTIONS['only_depth'][0]=0
        else :
            self.ssao.SSAO_OPTIONS['only_depth'][0]=1

    def set_options(self,name,value):
        if self.ssao.SSAO_OPTIONS[name][3] == "int" :
            self.ssao.SSAO_OPTIONS[name][0]=int(value)
        else :
            self.ssao.SSAO_OPTIONS[name][0]=float(value)
        cmd.refresh_wizard()

    def get_panel(self):
        if not hasattr(self,'dismiss'):
            self.dismiss=1
        if self.dismiss==1:
            panel_setup=[]
            panel_setup.append([ 1, 'Parameters', '' ])
            for k in self.ssao.SSAO_OPTIONS_ORDER:
                panel_setup.append([ 3, "%s: %3.1f"%(k,self.ssao.SSAO_OPTIONS[k][0]), k ])
            return panel_setup
#        [
#                [ 1, 'Parameters', '' ],
#                [ 3, 'line_intensity', '' ],
#                [ 3, 'c_limit', '' ],
#                [ 3, 'c_spacing', '' ],
#                [ 3, 'c_width', '' ],
#                [ 3, 's_spacing', '' ],
#                [ 3, 's_width', '' ],
#                [ 3, 'd_spacing', '' ],
#                [ 3, 'd_width_high', '' ],
#                [ 3, 'd_width_low', '' ],
#                [ 3, 'g_low', '' ],
#                [ 3, 'g_hight', '' ],
#                [ 3, 'l_low', '' ],
#                [ 3, 'l_hight', '' ],
#                [ 3, 'd_width_spread', '' ],
#                [ 2, 'ssao_only', 'param.setssao_only()' ],
#                [ 2, 'only_depth', 'param.setonly_depth()' ],
#                [ 3, "back_intensity: %3.1f"%self.ssao.SSAO_OPTIONS['back_intensity'][0],'back_intensity'],
#                [ 2, 'Dismiss', 'cmd.set_wizard()' ]
#                ]
        else:
            return []

class myCallback(Callback,Wizard):

    def __init__(self):
        self.copy_depth_ssao = True
        self._width, self._height = cmd.get_session()['main'][0:2]
        self.m = cmd.get_view(0)
        self.near = self.m[15]
        self.far = self.m[16]
        self.use_mask_depth=0
        self.ssao_method = 1
        self.setShaderSSAO()


    def defaultShader(self):
        self.VERTEX_SHADER = shaders.compileShader("""#version 120
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }""", GL_VERTEX_SHADER)
        self.FRAGMENT_SHADER = shaders.compileShader("""#version 120
        void main() {
            gl_FragColor = vec4( 0, 1, 0, 1 );
        }""", GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(self.VERTEX_SHADER,self.FRAGMENT_SHADER)
        self.vbo = vbo.VBO(
            np.array( [
                [  0, 1, 0 ],
                [ -1,-1, 0 ],
                [  1,-1, 0 ],
                [  2,-1, 0 ],
                [  4,-1, 0 ],
                [  4, 1, 0 ],
                [  2,-1, 0 ],
                [  4, 1, 0 ],
                [  2, 1, 0 ],
            ],'f')
        )

        self.callback_name = cmd.get_unused_name('_cb')

    def setDefaultSSAO_OPTIONS(self):

        self.SSAO_OPTIONS={'far': [300.0,0.,1000.,"float"],
                'near': [self.near,0.,100.,"float"],
                'method':[self.ssao_method,0,2,"int"],
                'do_noise':[0,0,1,"int"],
                'fog':[0,0,1,"int"],
                'use_fog':[1,0,1,"int"],
                'use_mask_depth':[self.use_mask_depth,0,1,"int"],
                'only_depth':[0,0,1,"int"],
                'mix_depth':[0,0,1,"int"],
                'only_ssao':[1,-1,1,"int"],
                'show_mask_depth':[0,0,1,"int"],
                'scale':[1.0,1.0,100.0,"float"],
                'samples': [6,1,8,"int"],
                'rings': [6,1,8,"int"],
                'aoCap': [1.2,0.0,10.0,"float"],
                'aoMultiplier': [200.0,1.,500.,"float"],
                'depthTolerance': [0.0,0.0,1.0,"float"],
                'aorange':[60.0,1.0,500.0,"float"],
                'negative':[0,0,1,"int"],
                'correction':[6.0,0.0,1000.0,"float"],
                #'force_real_far':[0,0,1,"int"],

                # Add by Pierrick
                'back_intensity': [1.0,0.0,1.0,"float"],
                'line_intensity': [0.0,0.0,1.0,"float"],
                'c_limit': [0.6,0.0,1.0,"float"],
                'c_spacing': [2.0,0.0,100.0,"float"],
                'c_width': [10.0,0.0,100.0,"float"],
                's_spacing': [6.0,0.0,10.0,"float"],
                's_width': [1.0,0.0,100.0,"float"],
                'd_spacing': [4.0,0.0,10.0,"float"],
                'd_width_high': [0.0,0.0,1.0,"float"],
                'd_width_low': [0.0,0.0,10.0,"float"],
                'g_low': [16000.0,0.0,1000000.0,"float"],
                'g_hight': [17000.0,0.0,1000000.0,"float"],
                'l_low': [5000.0,0.0,1000000.0,"float"],
                'l_hight': [10000.0,0.0,1000000.0,"float"],
                'd_width_spread': [1.0,0.0,100.0,"float"],
                'zl_max': [0.0,0.0,1.0,"float"],
                'zl_min': [0.0,0.0,1.0,"float"],
#                'back_intensity': [1.0,0.0,1.0,"float"],
#                'line_intensity': [0.0,0.0,1.0,"float"],
#                'c_limit': [0.6,0.0,1.0,"float"],
#                'c_spacing': [2.0,0.0,100.0,"float"],
#                'c_width': [10.0,0.0,100.0,"float"],
#                's_spacing': [6.0,0.0,10.0,"float"],
#                's_width': [1.0,0.0,100.0,"float"],
#                'd_spacing': [4.0,0.0,10.0,"float"],
#                'd_width_high': [0.0,0.0,1.0,"float"],
#                'd_width_low': [0.0,0.0,10.0,"float"],
#                'g_low': [16000.0,0.0,1000000.0,"float"],
#                'g_hight': [17000.0,0.0,1000000.0,"float"],
#                'l_low': [5000.0,0.0,1000000.0,"float"],
#                'l_hight': [10000.0,0.0,1000000.0,"float"],
#                'd_width_spread': [1.0,0.0,100.0,"float"],
#                'zl_max': [0.0,0.0,1.0,"float"],
#                'zl_min': [0.0,0.0,1.0,"float"],
                # End Add by Pierrick
                }
        self.SSAO_OPTIONS["near"][0] = 2.0
        #self.Set(near = 2.0)
        self.SSAO_OPTIONS_ORDER = ['method', 'only_ssao','only_depth','mix_depth',
				'negative','do_noise','near','scale','rings','samples','aoCap','aoMultiplier',
				'aorange','depthTolerance','use_mask_depth']#'far','correction',


    def setTextureSSAO(self):
        self.depthtextureName = int(glGenTextures(1))
        glPrioritizeTextures(1,[self.depthtextureName],1)
        #glPrioritizeTextures(np.array([self.depthtextureName]),
        #                     np.array([1.]))
        glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        glTexImage2D (GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, self._width,
                      self._height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None);
        #SSAO depthexture
        self.illumtextureName = int(glGenTextures(1))
        glPrioritizeTextures(1,[self.illumtextureName],1)
        #glPrioritizeTextures(np.array([self.illumtextureName]),
        #                     np.array([1.]))
        glBindTexture (GL_TEXTURE_2D, self.illumtextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        glTexImage2D (GL_TEXTURE_2D, 0, GL_LUMINANCE, self._width,
                      self._height, 0, GL_LUMINANCE, GL_UNSIGNED_INT, None);

        #SSAO depthexture
        self.rendertextureName = int(glGenTextures(1))
        glPrioritizeTextures(1,[self.rendertextureName],1)
        #glPrioritizeTextures(np.array([self.rendertextureName]),
        #                     np.array([1.]))
        glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        glTexImage2D (GL_TEXTURE_2D, 0, GL_RGB, self._width,
                      self._height, 0, GL_RGB, GL_UNSIGNED_INT, None);
        #depth mask texture
        self.depthmasktextureName = int(glGenTextures(1))
        glPrioritizeTextures(1,[self.depthmasktextureName],1)
        #glPrioritizeTextures(np.array([self.depthmasktextureName]),
        #                     np.array([1.]))
        glBindTexture (GL_TEXTURE_2D, self.depthmasktextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        glTexImage2D (GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, self._width,
                      self._height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None);
        #SSAO randomtexture
#
#        self.randomTexture = Texture()
#        import Image
#        img = Image.open(DejaVu2.__path__[0]+os.sep+"textures"+os.sep+"random_normals.png")
#        self.randomTexture.Set(enable=1, image=img)
        self.randomtextureName = int(glGenTextures(1))
        glPrioritizeTextures(1,[self.randomtextureName],1)
        #glPrioritizeTextures(np.array([self.randomtextureName]),
        #                     np.array([1.]))
#        _gllib.glBindTexture (GL_TEXTURE_2D, self.randomtextureName);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
#        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
#        _gllib.glTexImage2D (GL_TEXTURE_2D, 0, self.randomTexture.format,
#                             self.randomTexture._width, self.randomTexture._height,
#                             0, self.randomTexture.format, GL_UNSIGNED_INT,
#                             self.randomTexture.image);

#        self.shadowmaptexture = int(glGenTextures(1))
#        glPrioritizeTextures(1,[self.shadowmaptexture],1)
#        #glPrioritizeTextures(np.array([self.depthmasktextureName]),
#        #                     np.array([1.]))
#        glBindTexture (GL_TEXTURE_2D, self.shadowmaptexture);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
#        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
#        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
#        glTexImage2D (GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, 512,
#                     512, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None);
        #SSAO randomtexture
        glBindTexture (GL_TEXTURE_2D,0)

    def setShaderSSAO(self):
        self.setDefaultSSAO_OPTIONS()
        self.setTextureSSAO()
        #f = _glextlib.glCreateShader(GL_FRAGMENT_SHADER)
        sfile = open(os.getcwd()+os.sep+"shaders"+os.sep+"fragSSAO","r")
        lines = sfile.readlines()
        sfile.close()
        self.fragmentSSAOShaderCode=""
        for l in lines :
            self.fragmentSSAOShaderCode+=l
        self.FRAGMENT_SHADER = shaders.compileShader(self.fragmentSSAOShaderCode, GL_FRAGMENT_SHADER)
        #v = _glextlib.glCreateShader(GL_VERTEX_SHADER)
        sfile = open("shaders"+os.sep+"vertSSAO","r")
        lines = sfile.readlines()
        sfile.close()
        self.vertexSSAOShaderCode=""
        for l in lines :
            self.vertexSSAOShaderCode+=l
        self.VERTEX_SHADER = shaders.compileShader(self.vertexSSAOShaderCode, GL_VERTEX_SHADER)
        self.shader = shaders.compileProgram(self.VERTEX_SHADER,self.FRAGMENT_SHADER)

        self.SSAO_LOCATIONS = {
            'RandomTexture': glGetUniformLocation( self.shader, 'RandomTexture' ),
            'DepthTexture': glGetUniformLocation( self.shader, 'DepthTexture' ),
            'RenderedTexture': glGetUniformLocation( self.shader, 'RenderedTexture' ),
            'LuminanceTexture': glGetUniformLocation( self.shader, 'LuminanceTexture' ),
            'DepthMaskTexture': glGetUniformLocation( self.shader, 'DepthMaskTexture' ),
            'RenderedTextureWidth':glGetUniformLocation( self.shader, 'RenderedTextureWidth' ),
            'RenderedTextureHeight': glGetUniformLocation( self.shader, 'RenderedTextureHeight' ),
            'realfar': glGetUniformLocation( self.shader, 'realfar' ),
            'ShadowTexture':glGetUniformLocation(self.shader,'ShadowTexture'),
            #'realnear': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'realnear' ),
#                'fogS': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'fogS' ),
#                'fogE': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'fogE' ),
            }

        for k in self.SSAO_OPTIONS :
                self.SSAO_LOCATIONS[k] = glGetUniformLocation( self.shader, k )

    def copyDepth(self):
        glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
        glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, self._width, self._height, 0);
        self.copy_depth_ssao = False


    def copyBuffer(self, depthmask=False):
        if depthmask :
            glBindTexture (GL_TEXTURE_2D, self.depthmasktextureName);
            glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, self._width, self._height, 0);
            return
        if self.copy_depth_ssao :
            glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
            glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, self._width,self._height, 0);

        glBindTexture (GL_TEXTURE_2D, self.illumtextureName);
        glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, 0, 0, self._width,
                      self._height, 0);

        glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
        glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 0, 0, self._width,self._height, 0);
        glBindTexture (GL_TEXTURE_2D, 0);

    def DrawShadow(self,):

#        glBindFramebuffer(GL_FRAMEBUFFER, 0 )
        #draw scene from point of view of Light
        #glViewport(0, 0, shadowMapSize, shadowMapSize);
        #self.camera = [self.m[9], self.m[10], self.m[11]]
        #self.center = [self.m[12], self.m[13], self.m[14]]
        cmd.set_view ([\
      self.lightViewMatrix[0][0],   self.lightViewMatrix[0][1],   self.lightViewMatrix[0][2],\
      self.lightViewMatrix[1][0],   self.lightViewMatrix[0][1],   self.lightViewMatrix[0][2],\
      self.lightViewMatrix[2][0],   self.lightViewMatrix[0][1],   self.lightViewMatrix[0][2],\
       self.lightPosition[0], self.lightPosition[1], self.lightPosition[2],\
       11.842411041,   20.648729324,    8.775371552,\
       2,  8,    0.000000000 ])
       # glMatrixMode(GL_PROJECTION);
       # glLoadMatrixf(self.lightProjectionMatrix);

       # glMatrixMode(GL_MODELVIEW);
       # glLoadMatrixf(self.lightViewMatrix);

        #se viewport the same size as the shadow map
        #glViewport(0, 0, shadowMapSize, shadowMapSize);
       # glViewport(0,0,shadowMapSize,shadowMapSize)
        cmd.draw(512)
        #//Read the depth buffer into the shadow map texture
        glBindTexture(GL_TEXTURE_2D, self.shadowmaptexture);
        glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, 512,512, 0);
        glBindTexture (GL_TEXTURE_2D, 0);
        cmd.set_view(self.m)

#        glMatrixMode(GL_PROJECTION);
#        glLoadMatrixf(self.cameraProjectionMatrix);
#        glMatrixMode(GL_MODELVIEW);
#        glLoadMatrixf(self.cameraViewMatrix);
#
#        glMatrixMode(GL_PROJECTION);
#        glPopMatrix();
#        glMatrixMode(GL_MODELVIEW);
#        glPopMatrix();

    def CalculateMatrix(self):
        #//Calculate & save matrices
        #self._width, self._height = cmd.get_session()['main'][0:2]
        #self.m = cmd.get_view(0)
        #view = cmd.get_view()
        #glPushMatrix()
        glLoadIdentity();
        gluPerspective(45.0, float(self._width/self._height),self.near, self.far);#//fovy, aspect,near,far
        self.cameraProjectionMatrix = glGetFloatv(GL_MODELVIEW_MATRIX);

        glLoadIdentity();
        gluLookAt(self.camera[0], self.camera[1], self.camera[2],
        0.0, 0.0, 0.0,
        0.0, 1.0, 0.0);
        self.cameraViewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX);

        glLoadIdentity();
        gluPerspective(45.0, 1.0, 2.0, 8.0);
        self.lightProjectionMatrix = glGetFloatv(GL_MODELVIEW_MATRIX);

        self.lightPosition = eval(cmd.get("light"))

        glLoadIdentity();
        gluLookAt( self.lightPosition[0], self.lightPosition[1], self.lightPosition[2],
        0.0, 0.0, 0.0,
        0.0, 1.0, 0.0);
        self.lightViewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX);
        #glPopMatrix();


    def drawSSAO(self,combine=0):
        #if not self.AR.use_mask:
        self.copyBuffer()
        glBindFramebuffer(GL_FRAMEBUFFER, 0 )
        shaders.glUseProgram( self.shader )

        glActiveTexture(GL_TEXTURE3);
        glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
        glUniform1i(self.SSAO_LOCATIONS['DepthTexture'],3)

        glActiveTexture(GL_TEXTURE4);
        glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
        glUniform1i(self.SSAO_LOCATIONS['RenderedTexture'],4)

        glActiveTexture(GL_TEXTURE5);
        glBindTexture (GL_TEXTURE_2D, self.illumtextureName);
        glUniform1i(self.SSAO_LOCATIONS['LuminanceTexture'],5)

        glActiveTexture(GL_TEXTURE6);
        glBindTexture (GL_TEXTURE_2D, self.randomtextureName);
        glUniform1i(self.SSAO_LOCATIONS['RandomTexture'],6)

        glActiveTexture(GL_TEXTURE7);
        glBindTexture (GL_TEXTURE_2D, self.depthmasktextureName);
        glUniform1i(self.SSAO_LOCATIONS['DepthMaskTexture'],7)
#
#        glActiveTexture(GL_TEXTURE8);
#        glBindTexture (GL_TEXTURE_2D, self.shadowmaptexture);
#        glUniform1i(self.SSAO_LOCATIONS['ShadowTexture'],7)


        glUniform1f(self.SSAO_LOCATIONS['RenderedTextureWidth'],self._width)
        glUniform1f(self.SSAO_LOCATIONS['RenderedTextureHeight'],self._height)

        glUniform1f(self.SSAO_LOCATIONS['realfar'],self.far)
        #_glextlib.glUniform1f(self.SSAO_LOCATIONS['realnear'],self.near)

        #zl=glReadPixels(0, 18, self._width, self._height,GL_DEPTH_COMPONENT, GL_FLOAT)

        for k in self.SSAO_OPTIONS:
            val = self.SSAO_OPTIONS[k][0]
            if k == "correction" :
                val = self.SSAO_OPTIONS[k][0]
                self.SSAO_OPTIONS[k][0] = val = self.far / 10.0
                #if len(self.SSAO_OPTIONS[k]) == 5 :
                #    val = self.SSAO_OPTIONS[k][-1].get()
            if k == "far" :
                #val = self.SSAO_OPTIONS[k][0]
                val = self.far + 230.
                #if len(self.SSAO_OPTIONS[k]) == 5 :
                #    val = self.SSAO_OPTIONS[k][-1].get()
            if k == "fog" :
                self.SSAO_OPTIONS[k][0] = val = 0#int(self.fog.enabled)
                #if len(self.SSAO_OPTIONS[k]) == 5 :
                #    self.SSAO_OPTIONS[k][-1].set(val)
#            if k == "zl_min" :
#                self.SSAO_OPTIONS[k][0] = val = np.amin(zl)
#                # print "min",self.SSAO_OPTIONS[k][0]
#            if k == "zl_max" :
#                self.SSAO_OPTIONS[k][0] = val = np.amax(zl)
                # print "max",self.SSAO_OPTIONS[k][0]
            if self.SSAO_OPTIONS[k][3] == "float":
                glUniform1f(self.SSAO_LOCATIONS[k],val)
            else :
                glUniform1i(self.SSAO_LOCATIONS[k],val)
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT |GL_STENCIL_BUFFER_BIT) # problem rajoute une visu en lines
        self.drawTexturePolygon()
        self.endSSAO()

    def endSSAO(self):
            glUseProgram(0)
            glActiveTexture(GL_TEXTURE0);
            glBindTexture (GL_TEXTURE_2D, 0);

    def drawTexturePolygon(self):
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        lViewport = glGetIntegerv(GL_VIEWPORT)
        glOrtho(float(lViewport[0]),
                float(lViewport[0]+lViewport[2]),
                float(lViewport[1]),
                float(lViewport[1]+lViewport[3]),
                -1, 1)
        glEnable(GL_BLEND)

#        glEnable(GL_TEXTURE_2D)
#        if self.dsT == 0 :
#            _gllib.glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
#        elif self.dsT == 1 :
#            _gllib.glBindTexture (GL_TEXTURE_2D, self.illumtextureName);
#        else :
#            _gllib.glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
        glBegin(GL_POLYGON)
        glTexCoord2i(0, 0)
        glVertex2i(0, 0)
        glTexCoord2i(1, 0)
        glVertex2i(self._width, 0)
        glTexCoord2i(1, 1)
        glVertex2i(self._width, self._height)
        glTexCoord2i(0, 1)
        glVertex2i(0, self._height)
        glEnd()
        glDisable(GL_BLEND)
        glBindTexture (GL_TEXTURE_2D, 0);
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def load(self):
        cmd.load_callback(self, self.callback_name)


    def __call__(self):
        self._width, self._height = cmd.get_session()['main'][0:2]
        self.m = cmd.get_view(0)
        self.near = self.m[15]
        self.far = self.m[16]
        self.camera = [self.m[9], self.m[10], self.m[11]]
        self.center = [self.m[12], self.m[13], self.m[14]]
        #self.CalculateMatrix()
        #self.DrawShadow()
        self.drawSSAO()

    def default_call(self):
        shaders.glUseProgram(self.shader)
        try:
            self.vbo.bind()
            try:
                glEnableClientState(GL_VERTEX_ARRAY);
                glVertexPointerf( self.vbo )
                glDrawArrays(GL_TRIANGLES, 0, 9)
            finally:
                self.vbo.unbind()
                glDisableClientState(GL_VERTEX_ARRAY);
        finally:
            shaders.glUseProgram( 0 )

    def get_panel(self):
        return [
            [ 1, 'Plane Wizard',''],
            [ 2, 'Reset',''],
            [ 2, 'Delete All Planes' , ''],
            [ 2, 'Done',''],
        ]

ob = myCallback()
cmd.load_callback(ob, "ssao")
cmd.orient()
cmd.zoom()
cmd.clip("near","100000")
cmd.clip("far","-100000")
param = Parameters(ssao=ob)
cmd.set_wizard(param)
