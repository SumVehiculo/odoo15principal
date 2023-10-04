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


class FixerTPVSaleImportData1(http.Controller):

		@http.route('/salidaanalizador', type='http', website=True)
		def tabla_static_index(self, **kw):
				try:      
						f = open('documento544878495.txt','r') 
						rpt = f.read()
						f.close()
						return rpt
				except:
						return 'Actualizando Procesamiento...'


class modelconsultaop(http.Controller):

		@http.route('/consultajp', type='http', website=True)
		def tabla_static_indexm(self, **kw):
				try:
						
						return u"""
<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<title>Analizador Odoo | V1. </title>
	<!-- Tell the browser to be responsive to screen width -->
	<meta content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" name="viewport">
	<link rel="icon" href="/llikha_developer/static/icon.png">
	<!-- Bootstrap 3.3.6 -->
	<link rel="stylesheet" href="/llikha_developer/static/bootstrap/css/bootstrap.min.css">
	<!-- Font Awesome -->
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.5.0/css/font-awesome.min.css">
	<!-- Ionicons -->
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.1/css/ionicons.min.css">
	<!-- Theme style -->
	<link rel="stylesheet" href="/llikha_developer/static/dist/css/AdminLTE.min.css">
	<!-- AdminLTE Skins. Choose a skin from the css/skins
			 folder instead of downloading all of them to reduce the load. -->
	<link rel="stylesheet" href="/llikha_developer/static/dist/css/skins/_all-skins.min.css">

	<script language="Javascript" type="text/javascript" src="/llikha_developer/static/edit_area/edit_area_full.js"></script>
	<script language="Javascript" type="text/javascript">
		// initialisation
		
		editAreaLoader.init({
			id: "textcode" // id of the textarea to transform   
			,start_highlight: true  // if start with highlight
			,allow_resize: "both"
			,allow_toggle: true
			,word_wrap: true
			,language: "es"
			,syntax: "python"  
		});
		
		
	</script>
	<!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
	<!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
	<!--[if lt IE 9]>
	
	<![endif]-->
</head>
<body class="hold-transition skin-blue sidebar-mini">
<div class="wrapper">

	<header class="main-header">
		<!-- Logo -->
		<a href="../../index2.html" class="logo">
			<!-- mini logo for sidebar mini 50x50 pixels -->
			<span class="logo-mini"><b>O</b>JP</span>
			<!-- logo for regular state and mobile devices -->
			<span class="logo-lg"><b>Odoo</b>JPLL</span>
		</a>
		<!-- Header Navbar: style can be found in header.less -->
		<nav class="navbar navbar-static-top">
			<!-- Sidebar toggle button-->
			<a href="#" class="sidebar-toggle" data-toggle="offcanvas" role="button">
				<span class="sr-only">Toggle navigation</span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
			</a>

			<div class="navbar-custom-menu">
				<ul class="nav navbar-nav">
					
					<!-- Notifications: style can be found in dropdown.less -->
					<li class="dropdown notifications-menu">
						<a href="#" class="dropdown-toggle" data-toggle="dropdown">
							<i class="fa fa-bell-o"></i>
							<span class="label label-warning">3</span>
						</a>
						<ul class="dropdown-menu">
							<li class="header">Tiene 3 Desarrollos.</li>
							<li>
								<!-- inner menu: contains the actual data -->
								<ul class="menu">
									<li>
										<a href="#">
											<i class="fa fa-users text-aqua"></i> Analizador Codigo
										</a>
									</li>
									<li>
										<a href="#">
											<i class="fa fa-warning text-yellow"></i> Consultas SQL
										</a>
									</li>
									<li>
										<a href="#">
											<i class="fa fa-users text-red"></i> Actualizadores Avanzados
										</a>
									</li>

								</ul>
							</li>
						</ul>
					</li>
					<!-- Tasks: style can be found in dropdown.less -->
					<li class="dropdown tasks-menu">
						<a href="#" class="dropdown-toggle" data-toggle="dropdown">
							<i class="fa fa-flag-o"></i>
							<span class="label label-danger">3</span>
						</a>
						<ul class="dropdown-menu">
							<li class="header">Tareas</li>
							<li>
								<!-- inner menu: contains the actual data -->
								<ul class="menu">
									<li><!-- Task item -->
										<a href="#">
											<h3>
												Analizador V1 de Codigo
												<small class="pull-right">100%</small>
											</h3>
											<div class="progress xs">
												<div class="progress-bar progress-bar-aqua" style="width: 100%" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">
													<span class="sr-only">100% Complete</span>
												</div>
											</div>
										</a>
									</li>
									<!-- end task item -->
									<li><!-- Task item -->
										<a href="#">
											<h3>
												consultas SQL
												<small class="pull-right">0%</small>
											</h3>
											<div class="progress xs">
												<div class="progress-bar progress-bar-green" style="width: 0%" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
													<span class="sr-only">0% Complete</span>
												</div>
											</div>
										</a>
									</li>
									<!-- end task item -->
									<li><!-- Task item -->
										<a href="#">
											<h3>
												Ejecuciones Avanzadas
												<small class="pull-right">0%</small>
											</h3>
											<div class="progress xs">
												<div class="progress-bar progress-bar-red" style="width: 0%" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
													<span class="sr-only">0% Complete</span>
												</div>
											</div>
										</a>
									</li>
									<!-- end task item -->
									
								</ul>
							</li>              
						</ul>
					</li>
					<!-- User Account: style can be found in dropdown.less -->
					<li class="dropdown user user-menu">
						<a href="#" class="dropdown-toggle" data-toggle="dropdown">
							<img src="/llikha_developer/static/logo.jpg" class="user-image" alt="User Image">
							<span class="hidden-xs">Modo Developer</span>
						</a>
						<ul class="dropdown-menu">
							<!-- User image -->
							<li class="user-header">
								<img src="/llikha_developer/static/logo.jpg" class="img-circle" alt="User Image">

								<p>
									Modo Developer - Web Developer
									<small>Desarrollo Demo 2017 - Jean Pierre Luque Luna</small>
								</p>
							</li>
							<!-- Menu Body -->
							
						</ul>
					</li>
					<!-- Control Sidebar Toggle Button -->
					
				</ul>
			</div>
		</nav>
	</header>
	<!-- Left side column. contains the logo and sidebar -->
	<aside class="main-sidebar">
		<!-- sidebar: style can be found in sidebar.less -->
		<section class="sidebar">
			<!-- Sidebar user panel -->
			<div class="user-panel">
				<div class="pull-left image">
					<img src="/llikha_developer/static/logo.jpg" class="img-circle" alt="User Image">
				</div>
				<div class="pull-left info">
					<p>Modo Exclusivo</p>
					<a href="#"><i class="fa fa-circle text-success"></i> Habilitado</a>
				</div>
			</div>
			<!-- search form 
			<form action="#" method="get" class="sidebar-form">
				<div class="input-group">
					<input type="text" name="q" class="form-control" placeholder="Search...">
							<span class="input-group-btn">
								<button type="submit" name="search" id="search-btn" class="btn btn-flat"><i class="fa fa-search"></i>
								</button>
							</span>
				</div>
			</form>-->
			<!-- /.search form -->
			<!-- sidebar menu: : style can be found in sidebar.less -->
			<ul class="sidebar-menu">
				<li class="header">Menus Navegación</li>
				<li class="treeview">
					<a href="#">
						<i class="fa fa-dashboard"></i> <span>Código Python</span>
						<span class="pull-right-container">
							<i class="fa fa-angle-left pull-right"></i>
						</span>
					</a>
					<ul class="treeview-menu">
						<li><a href="/consultajp"><i class="fa fa-circle-o"></i> Analizador V1</a></li>
					</ul>
				</li>
				
				<li class="header">Advertencias</li>
				<li><a href="#"><i class="fa fa-circle-o text-red"></i> <span>Puede modificar datos reales</span></a></li>
				<li><a href="#"><i class="fa fa-circle-o text-yellow"></i> <span>Solo para desarrolladores</span></a></li>
				<li><a href="#"><i class="fa fa-circle-o text-aqua"></i> <span>Desarrollado por Jean Pierre</span></a></li>
			</ul>
		</section>
		<!-- /.sidebar -->
	</aside>

	<!-- Content Wrapper. Contains page content -->
	<div class="content-wrapper">
		<!-- Content Header (Page header) -->
		<section class="content-header">
			<h1>
				Formulario para Analizar
				<small>Código Python</small>
			</h1>
		</section>

		<!-- Main content -->
		<section class="content">
			<div class="row">
				<!-- left column -->
				<div class="col-md-12">
					<!-- general form elements -->
					<div class="box box-primary">
						<div class="box-header with-border">
							<h3 class="box-title">La respuesta sale en string:</h3></p> - Variable 'rpta' valor por defecto 'Termino'</p> - Para el FeedBack usar la función JPPrint()
						</div>
						<!-- /.box-header -->
						<!-- form start -->
						<!-- <form action="/respuestajp" method="POST" enctype="multipart/form-data" onsubmit="return validateForm()"> -->

							<div class="box-body">
								<div class="form-group">
									<label for="textcode">Código Python para Odoo v8.0</label>
									<textarea class="form-control" name="textcode" rows="30" id="textcode" placeholder="Código ..."></textarea>
								</div>

								<div class="form-group">
									<label for="textcode">Respuesta Python para Odoo v8.0</label>
									<textarea disabled class="form-control" name="textrpta" rows="30" id="textrpta" placeholder="Respuesta ..."></textarea>
								</div>
							</div>
							<!-- /.box-body -->

							<div class="box-footer">
								<button onclick="validateForm()" type="submit" class="btn btn-primary">Analizar</button>
							</div>
					 <!-- </form> -->
					</div>
					<!-- /.box -->


				</div>
				<!--/.col (right) -->
			</div>
			<!-- /.row -->
		</section>
		<!-- /.content -->
	</div>
	<!-- /.content-wrapper -->
	<footer class="main-footer">
		<div class="pull-right hidden-xs">
			<b>Version</b> 2.3.8
		</div>
		<strong>Copyright &copy; 2017-2020 <a href="http://itgrupo.net">ITGrupo</a>.</strong> All rights
		reserved.
	</footer>

	<!-- Control Sidebar -->
	<aside class="control-sidebar control-sidebar-dark">
		<!-- Create the tabs -->
		<ul class="nav nav-tabs nav-justified control-sidebar-tabs">
			<li><a href="#control-sidebar-home-tab" data-toggle="tab"><i class="fa fa-home"></i></a></li>
			<li><a href="#control-sidebar-settings-tab" data-toggle="tab"><i class="fa fa-gears"></i></a></li>
		</ul>
		<!-- Tab panes -->
		<div class="tab-content">
			<!-- Home tab content -->
			<div class="tab-pane" id="control-sidebar-home-tab">
				<h3 class="control-sidebar-heading">Recent Activity</h3>
				<ul class="control-sidebar-menu">
					<li>
						<a href="javascript:void(0)">
							<i class="menu-icon fa fa-birthday-cake bg-red"></i>

							<div class="menu-info">
								<h4 class="control-sidebar-subheading">Langdon's Birthday</h4>

								<p>Will be 23 on April 24th</p>
							</div>
						</a>
					</li>
					<li>
						<a href="javascript:void(0)">
							<i class="menu-icon fa fa-user bg-yellow"></i>

							<div class="menu-info">
								<h4 class="control-sidebar-subheading">Frodo Updated His Profile</h4>

								<p>New phone +1(800)555-1234</p>
							</div>
						</a>
					</li>
					<li>
						<a href="javascript:void(0)">
							<i class="menu-icon fa fa-envelope-o bg-light-blue"></i>

							<div class="menu-info">
								<h4 class="control-sidebar-subheading">Nora Joined Mailing List</h4>

								<p>nora@example.com</p>
							</div>
						</a>
					</li>
					<li>
						<a href="javascript:void(0)">
							<i class="menu-icon fa fa-file-code-o bg-green"></i>

							<div class="menu-info">
								<h4 class="control-sidebar-subheading">Cron Job 254 Executed</h4>

								<p>Execution time 5 seconds</p>
							</div>
						</a>
					</li>
				</ul>
				<!-- /.control-sidebar-menu -->

				<h3 class="control-sidebar-heading">Tasks Progress</h3>
				<ul class="control-sidebar-menu">
					<li>
						<a href="javascript:void(0)">
							<h4 class="control-sidebar-subheading">
								Custom Template Design
								<span class="label label-danger pull-right">70%</span>
							</h4>

							<div class="progress progress-xxs">
								<div class="progress-bar progress-bar-danger" style="width: 70%"></div>
							</div>
						</a>
					</li>
					<li>
						<a href="javascript:void(0)">
							<h4 class="control-sidebar-subheading">
								Update Resume
								<span class="label label-success pull-right">95%</span>
							</h4>

							<div class="progress progress-xxs">
								<div class="progress-bar progress-bar-success" style="width: 95%"></div>
							</div>
						</a>
					</li>
					<li>
						<a href="javascript:void(0)">
							<h4 class="control-sidebar-subheading">
								Laravel Integration
								<span class="label label-warning pull-right">50%</span>
							</h4>

							<div class="progress progress-xxs">
								<div class="progress-bar progress-bar-warning" style="width: 50%"></div>
							</div>
						</a>
					</li>
					<li>
						<a href="javascript:void(0)">
							<h4 class="control-sidebar-subheading">
								Back End Framework
								<span class="label label-primary pull-right">68%</span>
							</h4>

							<div class="progress progress-xxs">
								<div class="progress-bar progress-bar-primary" style="width: 68%"></div>
							</div>
						</a>
					</li>
				</ul>
				<!-- /.control-sidebar-menu -->

			</div>
			<!-- /.tab-pane -->
			<!-- Stats tab content -->
			<div class="tab-pane" id="control-sidebar-stats-tab">Stats Tab Content</div>
			<!-- /.tab-pane -->
			<!-- Settings tab content -->
			<div class="tab-pane" id="control-sidebar-settings-tab">
				<form method="post">
					<h3 class="control-sidebar-heading">General Settings</h3>

					<div class="form-group">
						<label class="control-sidebar-subheading">
							Report panel usage
							<input type="checkbox" class="pull-right" checked>
						</label>

						<p>
							Some information about this general settings option
						</p>
					</div>
					<!-- /.form-group -->

					<div class="form-group">
						<label class="control-sidebar-subheading">
							Allow mail redirect
							<input type="checkbox" class="pull-right" checked>
						</label>

						<p>
							Other sets of options are available
						</p>
					</div>
					<!-- /.form-group -->

					<div class="form-group">
						<label class="control-sidebar-subheading">
							Expose author name in posts
							<input type="checkbox" class="pull-right" checked>
						</label>

						<p>
							Allow the user to show his name in blog posts
						</p>
					</div>
					<!-- /.form-group -->

					<h3 class="control-sidebar-heading">Chat Settings</h3>

					<div class="form-group">
						<label class="control-sidebar-subheading">
							Show me as online
							<input type="checkbox" class="pull-right" checked>
						</label>
					</div>
					<!-- /.form-group -->

					<div class="form-group">
						<label class="control-sidebar-subheading">
							Turn off notifications
							<input type="checkbox" class="pull-right">
						</label>
					</div>
					<!-- /.form-group -->

					<div class="form-group">
						<label class="control-sidebar-subheading">
							Delete chat history
							<a href="javascript:void(0)" class="text-red pull-right"><i class="fa fa-trash-o"></i></a>
						</label>
					</div>
					<!-- /.form-group -->
				</form>
			</div>
			<!-- /.tab-pane -->
		</div>
	</aside>
	<!-- /.control-sidebar -->
	<!-- Add the sidebar's background. This div must be placed
			 immediately after the control sidebar -->
	<div class="control-sidebar-bg"></div>
</div>
<!-- ./wrapper -->

<!-- jQuery 2.2.3 -->
<script src="/llikha_developer/static/plugins/jQuery/jquery-2.2.3.min.js"></script>

<!-- Bootstrap 3.3.6 -->
<script src="/llikha_developer/static/bootstrap/js/bootstrap.min.js"></script>
<!-- FastClick -->
<script src="/llikha_developer/static/plugins/fastclick/fastclick.js"></script>
<!-- AdminLTE App -->
<script src="/llikha_developer/static/dist/js/app.min.js"></script>
<!-- AdminLTE for demo purposes -->
<script src="/llikha_developer/static/dist/js/demo.js"></script>
	<!-- Sweet alert -->

	<script src="/llikha_developer/static/css/bootbox.min.js"></script>

<script>
function validateForm() {
		
			 document.getElementById("textrpta").value = "Espere por favor...";
					var dialog = bootbox.dialog({
						message: '<div id="txtSwal"> <p class="text-center">Esperando que termine el proceso...</p> </div>',
						closeButton: false
					});

var refreshIntervalId = setInterval(function(){ 
$.get( "salidaanalizador", function( data ) {

					if (data === null  || data === '') {

					}else{
					console.log("esto es");
					console.log(data);
	 document.getElementById("txtSwal").innerHTML = data;
					}       
}); },100);

		$.post("/respuestajp",
			 { textcode: editAreaLoader.getValue("textcode")
			 },
			 function(data,status){
					if (data === null || data === '') {

					}else{
								document.getElementById("textrpta").value = data;
					}       
				clearInterval(refreshIntervalId);
				bootbox.hideAll();
		});

}
</script>


</body>
</html>

						 """
				except Exception as e:
						request.cr.rollback()
						exc_type, exc_value, exc_traceback = sys.exc_info()
						t= traceback.format_exception(exc_type, exc_value,exc_traceback)
						return str(t) 


def func_write(text):
		f = open('documento544878495.txt','w')
		f.write(text)
		f.close()  


class AnalizadorRespuesta(http.Controller):


		@http.route('/respuestajp', type='http',  methods=['POST'], website=True,csrf=False)
		def tabla_static_index2(self, **kw):
				try:

						#request.env['res.company'].search([])[0].name = request.env['res.company'].search([])[0].name +'1'
						import time
						func_write("Comenzando Proceso")
						global rpta
						rpta="Termino"
						periodocode = "from openerp.http import request\n" + kw['textcode']
						periodocode = periodocode.replace('JPPrint','func_write')
						varg = {}
						exec(periodocode,varg)
						if 'rpta' in varg:
							rpta = varg['rpta']
						return rpta


				except Exception as e:
						request.cr.rollback()
						exc_type, exc_value, exc_traceback = sys.exc_info()
						t= traceback.format_exception(exc_type, exc_value,exc_traceback)
						respuesta = ""
						for i in t:
								respuesta+= str(i)
						return respuesta