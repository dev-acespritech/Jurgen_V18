/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    get autoPrint() {
        return this.pos.config.enable_a4_printing || super.autoPrint;
    },
});