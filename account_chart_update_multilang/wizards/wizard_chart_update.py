# Copyright 2024 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import ormcache


class WizardUpdateChartsAccount(models.TransientModel):
    _inherit = "wizard.update.charts.accounts"

    @ormcache("self.lang")
    def _other_langs(self):
        return self.env["res.lang"].search([("code", "!=", self.lang)]).mapped("code")

    def _update_other_langs(self, templates):
        for _, tpl_xmlid in templates.get_external_id().items():
            template = self.env.ref(tpl_xmlid)
            module, xmlid = tpl_xmlid.split(".", 1)
            rec_xmlid = f"{module}.{self.company_id.id}_{xmlid}"
            rec = self.env.ref(rec_xmlid)
            for lang in self._other_langs():
                lang_tpl = template.with_context(lang=lang)
                for key in self._diff_translate_fields(template, rec):
                    lang_rec = rec.with_context(lang=lang)
                    lang_rec[key] = lang_tpl[key]

    def _diff_translate_fields(self, template, real):
        """Find differences by comparing the translations of the fields."""
        res = {}
        to_include = self.fields_to_include(template._name)
        for key in template._fields:
            if not template._fields[key].translate or key not in to_include:
                continue
            for lang in self._other_langs():
                template_trans = getattr(template.with_context(lang=lang), key)
                real_trans = getattr(real.with_context(lang=lang), key)
                if template_trans != real_trans:
                    res[key] = template[key]
        return res

    def diff_fields(self, template, real):
        """Compare template and real translations too."""
        res = super().diff_fields(template, real)
        res.update(self._diff_translate_fields(template, real))
        return res

    def _update_taxes(self):
        """Update the taxes with their template translations."""
        res = super()._update_taxes()
        self._update_other_langs(self.tax_ids.tax_id)
        return res

    def _update_fiscal_positions(self):
        """Update the fiscal positions with their template translations."""
        res = super()._update_fiscal_positions()
        self._update_other_langs(self.fiscal_position_ids.fiscal_position_id)
        return res
