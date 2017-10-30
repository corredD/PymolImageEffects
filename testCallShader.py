# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 13:38:08 2017

@author: ludov
"""
import os
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGL.GL import shaders

#from pymol.opengl.gl import *
from pymol.callback import Callback
from pymol.wizard import Wizard
from pymol import cmd
import numpy

cmd.fetch("1crn", async=0)
cmd.show("spheres","1crn")

class myCallback(Callback,Wizard):
    
    def __init__(self):
        self.copy_depth_ssao = True
        self._width, self._height = cmd.get_session()['main'][0:2]
        self.m = cmd.get_view(0)
        self.near = self.m[15]
        self.far = self.m[16]
        self.use_mask_depth=0
        self.ssao_method = 0
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
            numpy.array( [
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
                'method':[self.ssao_method,0,1,"int"],
                'do_noise':[0,0,1,"int"],
                'fog':[0,0,1,"int"],
                'use_fog':[1,0,1,"int"],
                'use_mask_depth':[self.use_mask_depth,0,1,"int"],
                'only_depth':[0,0,1,"int"],
                'mix_depth':[0,0,1,"int"],
                'only_ssao':[1,0,1,"int"],
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
                }
        self.SSAO_OPTIONS["near"][0] = 2.0
        #self.Set(near = 2.0)
        self.SSAO_OPTIONS_ORDER = ['use_fog','only_ssao','only_depth','mix_depth',
				'negative','do_noise','near','scale','rings','samples','aoCap','aoMultiplier',
				'aorange','depthTolerance','use_mask_depth']#'far','correction',


    def setTextureSSAO(self):
        self.depthtextureName = int(glGenTextures(1))
        glPrioritizeTextures(1,[self.depthtextureName],1)
        #glPrioritizeTextures(numpy.array([self.depthtextureName]),
        #                     numpy.array([1.]))
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
        #glPrioritizeTextures(numpy.array([self.illumtextureName]),
        #                     numpy.array([1.]))
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
        #glPrioritizeTextures(numpy.array([self.rendertextureName]),
        #                     numpy.array([1.]))
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
        #glPrioritizeTextures(numpy.array([self.depthmasktextureName]),
        #                     numpy.array([1.]))
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
        #glPrioritizeTextures(numpy.array([self.randomtextureName]),
        #                     numpy.array([1.]))
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
        glBindTexture (GL_TEXTURE_2D,0)
        
        
    def setShaderSSAO(self):
        self.setDefaultSSAO_OPTIONS()
        self.setTextureSSAO()
        #f = _glextlib.glCreateShader(GL_FRAGMENT_SHADER)
        sfile = open("shaders"+os.sep+"fragSSAO","r")
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

        glUniform1f(self.SSAO_LOCATIONS['RenderedTextureWidth'],self._width)
        glUniform1f(self.SSAO_LOCATIONS['RenderedTextureHeight'],self._height)
        
        glUniform1f(self.SSAO_LOCATIONS['realfar'],self.far)
        #_glextlib.glUniform1f(self.SSAO_LOCATIONS['realnear'],self.near)

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
            if self.SSAO_OPTIONS[k][3] == "float":
                glUniform1f(self.SSAO_LOCATIONS[k],val)
            else : 
                glUniform1i(self.SSAO_LOCATIONS[k],val)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT |GL_STENCIL_BUFFER_BIT) 
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
        
cmd.load_callback(myCallback(), "ssao")    
#cmd.set_wizard(myCallback())
