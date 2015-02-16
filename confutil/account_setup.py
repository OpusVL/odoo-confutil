# -*- coding: utf-8 -*-

##############################################################################
#
# Post-installation configuration helpers
# Copyright (C) 2015 OpusVL (<http://opusvl.com/>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""Common code for scripting installation of a chart of accounts
into a company.

The function you probably want to use is setup_company_accounts()
"""

from datetime import date

import logging
_logger = logging.getLogger(__name__)

def setup_company_accounts(cr, registry, uid, company, chart_template, code_digits=None, context=None):
    """This sets up accounts, fiscal year and periods for the given company.

    company: A res.company object
    chart_template: An account.chart.template object
    code_digits: The number of digits (the default is usually 6)
    context: e.g. {'lang': 'en_GB', 'tz': False, 'uid': openerp.SUPERUSER_ID}

    A financial year is set up starting this year on 1st Jan and ending this year on 31st Dec.
    """
    unconfigured_companies = unconfigured_company_ids(cr, registry, uid, context=context)
    if company.id in unconfigured_companies:
        setup_chart_of_accounts(cr, registry, uid,
            company_id=company.id,
            chart_template_id=chart_template.id,
            code_digits=code_digits,
            context=context,
        )

        today = date.today()
        fy_name = today.strftime('%Y')
        fy_code = 'FY' + fy_name
        account_start = today.strftime('%Y-01-01')
        account_end = today.strftime('%Y-12-31')

        create_fiscal_year(cr, registry, uid,
            company_id=company.id,
            name=fy_name,
            code=fy_code,
            start_date=account_start,
            end_date=account_end,
            context=context,
        )

def unconfigured_company_ids(cr, registry, uid, context=None):
    """Return list of ids of companies without a chart of accounts.
    """
    account_installer = registry['account.installer']
    return account_installer.get_unconfigured_cmp(cr, uid, context=context)

def setup_chart_of_accounts(cr, registry, uid, company_id, chart_template_id, code_digits=None, context=None):
    chart_wizard = registry['wizard.multi.charts.accounts']
    defaults = chart_wizard.default_get(cr, uid, ['bank_accounts_id', 'currency_id'], context=context)

    bank_accounts_spec = defaults.pop('bank_accounts_id')
    bank_accounts_id = [(0, False, i) for i in bank_accounts_spec]

    data = defaults.copy()
    data.update({
        "chart_template_id": chart_template_id,
        'company_id': company_id,
        'bank_accounts_id': bank_accounts_id,
    })

    onchange = chart_wizard.onchange_chart_template_id(cr, uid, [], data['chart_template_id'], context=context)
    data.update(onchange['value'])
    if code_digits:
        data.update({'code_digits': code_digits})

    conf_id = chart_wizard.create(cr, uid, data, context=context)
    chart_wizard.execute(cr, uid, [conf_id], context=context)

def create_fiscal_year(cr, registry, uid, company_id, name, code, start_date, end_date, context=None):
    fy_model = registry['account.fiscalyear']
    fy_data = fy_model.default_get(cr, uid, ['state', 'company_id'], context=context).copy()
    fy_data.update({
        'company_id': company_id,
        'name': name,
        'code': code,
        'date_start': start_date,
        'date_stop': end_date,
    })
    fy_id = fy_model.create(cr, uid, fy_data, context=context)
    fy_model.create_period(cr, uid, [fy_id], context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
