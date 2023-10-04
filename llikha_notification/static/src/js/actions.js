/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { sprintf } from "@web/core/utils/strings";
import { BlockUI } from "@web/core/ui/block_ui";
import { browser } from "@web/core/browser/browser";

const { utils, Component,tags, useState } = owl;
const { escape } = utils;

export const notificationLLikha = (env, action) => {
    const params = action.params || {};
    const buttonsadd = [];
    for(let i = 0; i < params.buttons.length; i++){
        var button_data = params.buttons[i];

        buttonsadd.push({
                                name: button_data.label,
                                primary: true,
                                onClick: async () => {
                                    var actionY = await env.services.rpc('/web/dataset/call_button',{
                                            model: button_data.model,
                                            method: button_data.method,
                                            args: [button_data.id],
                                            kwargs: {
                                                context: {}
                                            }            
                                        }).then(function (actionX) {
                                            env.services.action.doAction(actionX);
                                        })
                                } 
                        })
    };

    const options = {
        className: params.className || "",
        sticky: params.sticky || false,
        title: params.title,
        type: params.type || "info",
        messageIsHtml: true,
        buttons: buttonsadd,
    };
    let links = (params.links || []).map((link) => {
        return `<a href="${escape(link.url)}" target="_blank">${escape(link.label)}</a>`;
    });
    const message = params.message;
    env.services.notification.add(message, options);
    return params.next;
};

registry.category("actions").add("notification_llikha", notificationLLikha);


BlockUI.template = tags.xml`
    <div t-att-class="state.blockUI ? 'o_blockUI' : ''">
      <t t-if="state.blockUI">
        <div class="o_spinner">
            <img src="/web/static/img/spin.png" alt="Loading..."/>
        </div>
        <div class="o_message">
            <t t-raw="state.line1"/> <br/>
            <t t-raw="state.line2"/>
        </div>

        <div class="llikha_oe_throbber_message" style="width: 60% !important; text-align: center !important; color: white !important;">
        </div>
      </t>
    </div>`;