odoo.define('web.SwitchCompanyBranchMenu', function(require) {
	"use strict";
	
	var config = require('web.config');
	var core = require('web.core');
	var session = require('web.session');
	var SystrayMenu = require('web.SystrayMenu');
	var Widget = require('web.Widget');
	
	var _t = core._t;
	
	var SwitchCompanyBranchMenu = Widget.extend({
		template: 'SwitchCompanyBranchMenu',
		willStart: function() {
			if(config.device){
				this.isMobile = config.device.isMobile || false;
			}
			if (!session.user_companies) {
				return $.Deferred().reject();
			}
			return this._super();
		},
		init: function(parent){
			this._super(parent);
			this.isMobile = false;
			this.company_branch_addresss = [];
			this.current_company_branch_address_id = 0;
			this.current_company_branch_address_name = '';
		},
		start: function() {
			var self = this;
			this.$el.on('click', '.dropdown-menu div[data-menu]', _.debounce(function(ev) {
				ev.preventDefault();
				var company_id = $(ev.currentTarget).data('company-branch-id');
				self._rpc({
						model: 'res.users',
						method: 'write',
						args: [[session.uid], {'default_company_branch_address_id': company_id}],
					})
					.then(function() {
						location.reload();
					});
			}, 1500, true));
	
			self._rpc({
				model:'res.company.branch.address',
				method: 'get_session_info',
				args:[]
			}).then(function(data) {
				console.log("GET COMPANY BRANCH ++++++++++");
				console.log(data);
				var companies_list = '';
				if (self.isMobile) {
					companies_list = '<li class="bg-info">' + _t('Tap on the list to change company branch') + '</li>';
				}
				else {
					if(data.user_company_branch_addresss){
						self.$('.oe_topbar_name').text(data.user_company_branch_addresss.current_company_branch_address[1]);    
					}
				}
				if(data.user_company_branch_addresss){
					_.each(data.user_company_branch_addresss.allowed_company_branch_addresss, function(company) {
						var a = '';
						var b = '';
						var c = '';
						if (company[0] === data.user_company_branch_addresss.current_company_branch_address[0]) {
							a = 'fa fa-fw fa-check-square pt-2';							
							c = 'style="background-color: lightgrey;"';						                    
						} else {
							a ='fa fa-fw fa-square-o pt-2'; 
							b = 'text-muted';
						}
						companies_list += '<div class="dropdown-item d-flex py-0 px-0" data-menu="company_branch_address" data-company-branch-id="' + company[0] + '">' +
												'<div role="menuitemcheckbox" tabindex="0" class="ml-auto pl-3 pr-3 border border-top-0 border-left-0 border-bottom-0 toggle_company o_py">'+
													'<span style="height: 2rem;">'+									
															'<i class="'+a+'"/>'+								
													'</span>'+
												'</div>'+
												'<div  aria-label="Switch to this company" tabindex="0" class="d-flex flex-grow-1 align-items-center py-0 log_into pl-3 o_py" '+c+'>'+												
														'<span class="mr-3 company_label '+b+'">'+
																company[1]+
														'</span>'+											
												'</div>'+
											'</div>';
					});
					self.$('.dropdown-menu').html(companies_list);
				}else{
					console.log("ocultar select box");
					console.log(self);
					self.$el.hide();
				}
			});
			
			return this._super();
		},
	});
	
	SystrayMenu.Items.push(SwitchCompanyBranchMenu);
	
	return SwitchCompanyBranchMenu;
	
	});
	