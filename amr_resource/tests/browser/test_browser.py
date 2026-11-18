from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestIssuerBrowser(HttpCase):
    def test_lifecycle(self):
        issuer = self.env['oidc.issuer.register'].create({
            'issuer': 'https://browser-lifecycle.test', 'client_id': 'browser-client',
        })
        action = self.env.ref('amr_resource.action_resource_issuers')
        self.browser_js(
            '/web#id=%s&model=oidc.issuer.register&view_type=form&action=%s' % (issuer.id, action.id),
            """
            (async function () {
                function visible(el) { return el && el.offsetParent !== null; }
                async function wait(fn, label) {
                    for (var i = 0; i < 150; i++) {
                        var result = fn();
                        if (result) return result;
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                    throw new Error('Timeout: ' + label + ' DOM=' + (document.querySelector('.o_statusbar_status') || {}).outerHTML);
                }
                async function state(name, buttons) {
                    await wait(() => document.querySelector('.o_statusbar_status button[data-value="' + name + '"][aria-checked="true"]'), name);
                    for (var entry of Object.entries(buttons)) {
                        var button = document.querySelector('button[name="' + entry[0] + '"]');
                        if (!!visible(button) !== entry[1]) throw new Error(name + ': visibility ' + entry[0]);
                    }
                }
                async function click(name, target, buttons) {
                    (await wait(() => document.querySelector('button[name="' + name + '"]'), name)).click();
                    await state(target, buttons);
                }
                var draft = {action_to_production: true, action_to_draft: false, action_to_disable: true, unlink: false};
                var production = {action_to_production: false, action_to_draft: true, action_to_disable: true, unlink: false};
                var disable = {action_to_production: true, action_to_draft: true, action_to_disable: false, unlink: true};
                await state('draft', draft);
                (await wait(() => document.querySelector('.o_form_button_edit'), 'edit')).click();
                await wait(() => document.querySelector('.o_form_editable'), 'editable');
                var input = await wait(() => document.querySelector('input[name="client_id"]'), 'client input');
                input.value = 'browser-updated';
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
                document.querySelector('.o_form_button_save').click();
                await wait(() => document.querySelector('.o_form_readonly [name="client_id"]') && document.querySelector('.o_form_readonly [name="client_id"]').textContent === 'browser-updated', 'saved client');
                await click('action_to_production', 'production', production);
                document.querySelector('.o_form_button_edit').click();
                await wait(() => document.querySelector('.o_form_editable'), 'production edit');
                if (document.querySelector('input[name="client_id"]')) throw new Error('production client editable');
                document.querySelector('.o_form_button_cancel').click();
                await wait(() => document.querySelector('.o_form_readonly'), 'cancel');
                await click('action_to_draft', 'draft', draft);
                await click('action_to_disable', 'disable', disable);
                document.querySelector('.o_form_button_edit').click();
                await wait(() => document.querySelector('.o_form_editable'), 'disable edit');
                if (document.querySelector('input[name="client_id"]')) throw new Error('disable client editable');
                document.querySelector('.o_form_button_cancel').click();
                await wait(() => document.querySelector('.o_form_readonly'), 'disable cancel');
                await click('action_to_production', 'production', production);
                await click('action_to_disable', 'disable', disable);
                await click('action_to_draft', 'draft', draft);
                console.log('test successful');
            })().catch(error => console.error(error));
            """,
            login='admin', timeout=100,
        )

    def test_archive_reactivation(self):
        issuer = self.env['oidc.issuer.register'].create({
            'issuer': 'https://browser-archive.test', 'client_id': 'browser-client',
        })
        issuer.action_to_disable()
        action = self.env.ref('amr_resource.action_resource_issuers')
        self.browser_js(
            '/web#id=%s&model=oidc.issuer.register&view_type=form&action=%s' % (issuer.id, action.id),
            """
            (async function () {
                async function wait(fn, label) {
                    for (var i = 0; i < 150; i++) {
                        var value = fn();
                        if (value) return value;
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                    throw new Error('Timeout: ' + label + ' DOM=' + document.querySelector('.o_action_manager').innerHTML.slice(0, 12000));
                }
                async function archive() {
                    (await wait(() => document.querySelector('button[name="unlink"]'), 'archive')).click();
                    (await wait(() => document.querySelector('.modal-footer .btn-primary'), 'confirm')).click();
                    await wait(() => document.querySelector('.o_form_view [name="active"] input:not(:checked)'), 'archived');
                    document.querySelector('.breadcrumb-item a').click();
                    await wait(() => document.querySelector('.o_list_view') && document.querySelector('.o_list_view').offsetParent !== null, 'list after archive');
                    var search = await wait(() => document.querySelector('.o_searchview_input'), 'search');
                    search.focus();
                    search.value = 'https://browser-archive.test';
                    search.dispatchEvent(new Event('input', {bubbles: true}));
                    search.dispatchEvent(new KeyboardEvent('keyup', {key: 't', keyCode: 84, which: 84, bubbles: true}));
                    await wait(() => document.querySelector('.o_searchview_autocomplete li'), 'search suggestion');
                    search.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, which: 13, bubbles: true}));
                    await wait(() => document.querySelector('.o_searchview_facet'), 'search facet');
                    var row = await wait(() => Array.from(document.querySelectorAll('.o_data_row')).find(row => row.textContent.includes('https://browser-archive.test')), 'inactive row');
                    row.click();
                    await wait(() => document.querySelector('.o_form_view'), 'reopen');
                }
                async function transition(name, state) {
                    (await wait(() => document.querySelector('button[name="' + name + '"]'), name)).click();
                    await wait(() => document.querySelector('.o_statusbar_status button[data-value="' + state + '"][aria-checked="true"]'), state);
                    await wait(() => document.querySelector('.o_form_view [name="active"] input:checked'), 'reactivated');
                }
                await wait(() => document.querySelector('.o_statusbar_status button[data-value="disable"][aria-checked="true"]'), 'disable');
                await archive();
                var production = document.querySelector('button[name="action_to_production"]');
                if (production && production.offsetParent !== null) throw new Error('production visible on archived issuer');
                var archiveButton = document.querySelector('button[name="unlink"]');
                if (archiveButton && archiveButton.offsetParent !== null) throw new Error('archive visible on archived issuer');
                (await wait(() => Array.from(document.querySelectorAll('.o_cp_sidebar .dropdown-toggle')).find(button => button.textContent.trim() === 'Action'), 'action menu')).click();
                (await wait(() => Array.from(document.querySelectorAll('.dropdown-item')).find(item => item.textContent.trim() === 'Unarchive'), 'unarchive')).click();
                await wait(() => document.querySelector('.o_statusbar_status button[data-value="draft"][aria-checked="true"]'), 'unarchived draft');
                await transition('action_to_production', 'production');
                await transition('action_to_disable', 'disable');
                await transition('action_to_draft', 'draft');
                console.log('test successful');
            })().catch(error => console.error(error));
            """, login='admin', timeout=100,
        )
        issuer.invalidate_cache()
        self.assertEqual((issuer.state, issuer.active), ('draft', True))

    def test_children(self):
        issuer = self.env['oidc.issuer.register'].create({'issuer': 'https://browser-children.test', 'client_id': 'browser-client', 'resolver_mode': 'mapping'})
        user = self.env.ref('base.user_admin')
        algorithm = self.env['oidc.algorithm'].search([], limit=1)
        self.env['oidc.issuer.register.audience'].create({'issuer_id': issuer.id, 'value': 'audience-old'})
        self.env['oidc.issuer.subject'].create({'issuer_id': issuer.id, 'sub': 'subject-old', 'user_id': user.id})
        self.env['oidc.issuer.user.mapping'].create({'issuer_id': issuer.id, 'field_user': 'login', 'jwt_key': 'email'})
        self.env['oidc.issuer.algorithm.policy'].create({'issuer_id': issuer.id, 'algorithm_id': algorithm.id, 'enabled': True})
        action = self.env.ref('amr_resource.action_resource_issuers')
        self.browser_js(
            '/web#id=%s&model=oidc.issuer.register&view_type=form&action=%s' % (issuer.id, action.id),
            """
            (async function () {
                async function wait(fn, label) {
                    for (var i = 0; i < 150; i++) {
                        var value = fn();
                        if (value) return value;
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                    throw new Error('Timeout: ' + label + ' DOM=' + document.querySelector('.o_form_view').innerHTML.slice(-12000));
                }
                function tab(name) { Array.from(document.querySelectorAll('.nav-link')).find(el => el.textContent.trim() === name).click(); }
                async function editText(tabName, field, value) {
                    tab(tabName);
                    (await wait(() => document.querySelector('.tab-pane.active .o_data_cell'), 'row ' + field)).click();
                    var input = await wait(() => document.querySelector('.tab-pane.active input[name="' + field + '"]'), field);
                    input.value = value;
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
                (await wait(() => document.querySelector('.o_form_button_edit'), 'edit')).click();
                await wait(() => document.querySelector('.o_form_editable'), 'editable');
                await editText('Audiences', 'value', 'audience-new');
                await editText('Exact subject bindings', 'sub', 'subject-new');
                await editText('Ordered Claim Mappings', 'jwt_key', 'preferred_username');
                tab('Algorithm Policy');
                (await wait(() => document.querySelector('.tab-pane.active .o_data_cell'), 'policy row')).click();
                var checkbox = await wait(() => document.querySelector('.tab-pane.active [name="enabled"] input'), 'enabled');
                if (checkbox.checked) checkbox.click();
                if (checkbox.checked) throw new Error('policy checkbox did not uncheck: ' + checkbox.outerHTML);
                document.querySelector('.o_form_button_save').click();
                await wait(() => document.querySelector('.o_form_readonly'), 'saved');
                for (var state of ['production', 'disable']) {
                    document.querySelector('button[name="action_to_' + state + '"]').click();
                    await wait(() => document.querySelector('.o_statusbar_status button[data-value="' + state + '"][aria-checked="true"]'), state);
                    document.querySelector('.o_form_button_edit').click();
                    await wait(() => document.querySelector('.o_form_editable'), state + ' edit');
                    for (var pair of [['Audiences','audience_ids'], ['Exact subject bindings','binding_ids'], ['Ordered Claim Mappings','user_mapping_ids'], ['Algorithm Policy','algorithm_policy_ids']]) {
                        tab(pair[0]);
                        var widget = await wait(() => document.querySelector('.tab-pane.active [name="' + pair[1] + '"]'), pair[1]);
                        if (!widget.classList.contains('o_readonly_modifier') || widget.querySelector('.o_field_x2many_list_row_add')) throw new Error(state + ' child editable: ' + pair[1]);
                        var row = widget.querySelector('.o_data_cell');
                        if (row) row.click();
                        if (widget.querySelector('input:not([disabled]), select:not([disabled])')) throw new Error(state + ' child input: ' + pair[1]);
                    }
                    document.querySelector('.o_form_button_cancel').click();
                    await wait(() => document.querySelector('.o_form_readonly'), 'cancel');
                }
                console.log('test successful');
            })().catch(error => console.error(error));
            """, login='admin', timeout=100,
        )
        issuer.invalidate_cache()
        self.assertEqual(issuer.audience_ids.value, 'audience-new')
        self.assertEqual(issuer.binding_ids.sub, 'subject-new')
        self.assertEqual(issuer.user_mapping_ids.jwt_key, 'preferred_username')
        issuer.algorithm_policy_ids.invalidate_cache()
        self.assertFalse(issuer.algorithm_policy_ids.enabled)

    def test_nonadmin_access(self):
        issuer = self.env['oidc.issuer.register'].create({
            'issuer': 'https://browser-nonadmin.test', 'client_id': 'browser-client',
        })
        self.env['res.users'].create({
            'name': 'Browser ordinary', 'login': 'browser-ordinary', 'password': 'browser-ordinary',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        action = self.env.ref('amr_resource.action_resource_issuers')
        self.browser_js(
            '/web#id=%s&model=oidc.issuer.register&view_type=form&action=%s' % (issuer.id, action.id),
            """
            (async function () {
                for (var i = 0; i < 150; i++) {
                    var dialog = document.querySelector('.modal-dialog');
                    if (dialog && dialog.textContent.match(/access|permission|rights/i)) {
                        if (document.querySelector('.o_form_view button[name="action_to_production"]')) throw new Error('lifecycle button exposed');
                        console.log('test successful');
                        return;
                    }
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                throw new Error('Access denial not shown: ' + document.body.innerText.slice(0, 3000));
            })().catch(error => console.error(error));
            """, login='browser-ordinary', timeout=60,
        )

    def test_draft_form(self):
        action = self.env.ref('amr_resource.action_resource_issuers')
        self.assertEqual(self.env['oidc.issuer.register'].default_get(['state'])['state'], 'draft')
        self.browser_js(
            '/web#action=%s' % action.id,
            """
            (async function () {
                async function wait(fn, label) {
                    for (var i = 0; i < 150; i++) {
                        var value = fn();
                        if (value) return value;
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                    throw new Error('Timeout: ' + label + ' issuer=' + ((document.querySelector('[name="issuer"]') || {}).outerHTML) + ' state=' + ((document.querySelector('.o_statusbar_status') || {}).outerHTML));
                }
                (await wait(() => document.querySelector('.o_list_button_add'), 'create')).click();
                var issuer = await wait(() => document.querySelector('input[name="issuer"]'), 'issuer input');
                for (var pair of [[issuer, 'https://browser-created.test'], [document.querySelector('input[name="client_id"]'), 'created-client']]) {
                    pair[0].value = pair[1];
                    pair[0].dispatchEvent(new Event('input', {bubbles: true}));
                    pair[0].dispatchEvent(new Event('change', {bubbles: true}));
                }
                document.querySelector('.o_form_button_save').click();
                await wait(() => document.querySelector('.o_form_readonly [name="issuer"]') && document.querySelector('.o_form_readonly [name="issuer"]').textContent === 'https://browser-created.test', 'saved issuer');
                await wait(() => document.querySelector('.o_statusbar_status button[data-value="draft"][aria-checked="true"]'), 'draft');
                console.log('test successful');
            })().catch(error => console.error(error));
            """,
            login='admin', timeout=60,
        )
